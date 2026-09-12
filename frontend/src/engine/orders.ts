/**
 * Order and state management:
 * Deterministic client order IDs for idempotency, fill-only position truth,
 * and broker snapshot reconciliation. Matches src/orders.py identically.
 */
import { OrderItem } from '../types/quant';

function sha1(str: string): string {
  // Simple, fast pure JS SHA-1 implementation
  function rotateLeft(n: number, s: number) {
    return (n << s) | (n >>> (32 - s));
  }

  function cvtHex(val: number) {
    let str = "";
    for (let i = 7; i >= 0; i--) {
      const v = (val >>> (i * 4)) & 0x0f;
      str += v.toString(16);
    }
    return str;
  }

  const utf8: number[] = [];
  for (let i = 0; i < str.length; i++) {
    let charcode = str.charCodeAt(i);
    if (charcode < 0x80) utf8.push(charcode);
    else if (charcode < 0x800) {
      utf8.push(0xc0 | (charcode >> 6), 0x80 | (charcode & 0x3f));
    } else if (charcode < 0xd800 || charcode >= 0xe000) {
      utf8.push(0xe0 | (charcode >> 12), 0x80 | ((charcode >> 6) & 0x3f), 0x80 | (charcode & 0x3f));
    } else {
      i++;
      charcode = 0x10000 + (((charcode & 0x3ff) << 10) | (str.charCodeAt(i) & 0x3ff));
      utf8.push(
        0xf0 | (charcode >> 18),
        0x80 | ((charcode >> 12) & 0x3f),
        0x80 | ((charcode >> 6) & 0x3f),
        0x80 | (charcode & 0x3f)
      );
    }
  }

  const blockCount = ((utf8.length + 8) >> 6) + 1;
  const blocks: number[] = new Array(blockCount * 16).fill(0);
  for (let i = 0; i < utf8.length; i++) {
    blocks[i >> 2] |= utf8[i] << (24 - (i % 4) * 8);
  }
  blocks[utf8.length >> 2] |= 0x80 << (24 - (utf8.length % 4) * 8);
  blocks[blockCount * 16 - 1] = utf8.length * 8;

  let H0 = 0x67452301;
  let H1 = 0xefcdab89;
  let H2 = 0x98badcfe;
  let H3 = 0x10325476;
  let H4 = 0xc3d2e1f0;

  const W: number[] = new Array(80);
  for (let i = 0; i < blocks.length; i += 16) {
    for (let t = 0; t < 16; t++) W[t] = blocks[i + t];
    for (let t = 16; t < 80; t++) W[t] = rotateLeft(W[t - 3] ^ W[t - 8] ^ W[t - 14] ^ W[t - 16], 1);

    let A = H0;
    let B = H1;
    let C = H2;
    let D = H3;
    let E = H4;

    for (let t = 0; t < 80; t++) {
      let f = 0;
      let K = 0;
      if (t < 20) {
        f = (B & C) | (~B & D);
        K = 0x5a827999;
      } else if (t < 40) {
        f = B ^ C ^ D;
        K = 0x6ed9eba1;
      } else if (t < 60) {
        f = (B & C) | (B & D) | (C & D);
        K = 0x8f1bbcdc;
      } else {
        f = B ^ C ^ D;
        K = 0xca62c1d6;
      }
      const temp = (rotateLeft(A, 5) + f + E + K + W[t]) & 0xffffffff;
      E = D;
      D = C;
      C = rotateLeft(B, 30);
      B = A;
      A = temp;
    }

    H0 = (H0 + A) & 0xffffffff;
    H1 = (H1 + B) & 0xffffffff;
    H2 = (H2 + C) & 0xffffffff;
    H3 = (H3 + D) & 0xffffffff;
    H4 = (H4 + E) & 0xffffffff;
  }

  return (cvtHex(H0) + cvtHex(H1) + cvtHex(H2) + cvtHex(H3) + cvtHex(H4)).toLowerCase();
}

export function makeClientOrderId(strategyId: string, barIndex: number, intent: string): string {
  const raw = `${strategyId}|${barIndex}|${intent}`;
  return sha1(raw).substring(0, 16);
}

export class OrderManager {
  public orders: Map<string, OrderItem> = new Map();

  place(side: 'BUY' | 'SELL', qty: number, reason: string, barIndex: number, strategyId: string): OrderItem {
    const coid = makeClientOrderId(strategyId, barIndex, reason);
    if (this.orders.has(coid)) {
      return this.orders.get(coid)!; // Idempotent
    }
    const order: OrderItem = {
      client_order_id: coid,
      side,
      qty,
      reason,
      bar_index: barIndex,
      status: 'PENDING',
    };
    this.orders.set(coid, order);
    return order;
  }

  markFilled(clientOrderId: string, fillPrice: number, brokerOrderId: string) {
    const order = this.orders.get(clientOrderId);
    if (order) {
      order.status = 'FILLED';
      order.fill_price = fillPrice;
      order.broker_order_id = brokerOrderId;
    }
  }

  openOrders(): OrderItem[] {
    return Array.from(this.orders.values()).filter(o => o.status === 'PENDING');
  }

  reconcile(brokerSnapshot: Record<string, Partial<OrderItem>>): string[] {
    const notes: string[] = [];

    for (const [coid, remote] of Object.entries(brokerSnapshot)) {
      const local = this.orders.get(coid);
      if (!local) {
        notes.push(`adopted unknown order ${coid} from broker snapshot`);
        this.orders.set(coid, {
          client_order_id: coid,
          side: (remote.side as 'BUY' | 'SELL') || 'BUY',
          qty: remote.qty || 1.0,
          reason: remote.reason || 'recovered',
          bar_index: remote.bar_index ?? -1,
          status: remote.status || 'FILLED',
          fill_price: remote.fill_price,
          broker_order_id: remote.broker_order_id,
        });
        continue;
      }

      if (remote.status && local.status !== remote.status) {
        notes.push(
          `${coid}: local status ${local.status} != broker status ${remote.status}; adopting broker status`
        );
        local.status = remote.status;
        if (remote.fill_price !== undefined) local.fill_price = remote.fill_price;
        if (remote.broker_order_id) local.broker_order_id = remote.broker_order_id;
      }
    }

    return notes;
  }

  netPosition(): number {
    let pos = 0.0;
    for (const o of this.orders.values()) {
      if (o.status !== 'FILLED') continue;
      pos += o.side === 'BUY' ? o.qty : -o.qty;
    }
    return pos;
  }
}

