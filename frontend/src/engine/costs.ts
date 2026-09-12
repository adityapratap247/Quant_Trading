/**
 * Cost model: slippage + brokerage + statutory charges.
 * Matches src/costs.py down to the paisa.
 */
import { CostModel } from '../types/quant';

export class CostCalculator {
  constructor(public model: CostModel) {}

  slippedPrice(referencePrice: number, side: 'BUY' | 'SELL'): number {
    const adj = referencePrice * (this.model.slippage_bps / 10000.0);
    if (side === 'BUY') {
      return referencePrice + adj;
    } else if (side === 'SELL') {
      return referencePrice - adj;
    }
    throw new Error(`Unknown side: ${side}`);
  }

  totalCost(fillPrice: number, qty: number, side: 'BUY' | 'SELL'): number {
    const turnover = fillPrice * qty;
    const exch = turnover * (this.model.exchange_txn_bps / 10000.0);
    const stt = side === 'SELL' ? turnover * (this.model.stt_ctt_bps / 10000.0) : 0.0;
    const gst = (this.model.brokerage_per_order + exch) * this.model.gst_rate;
    return Number((this.model.brokerage_per_order + exch + stt + gst).toFixed(4));
  }

  breakdown(fillPrice: number, qty: number, side: 'BUY' | 'SELL') {
    const turnover = fillPrice * qty;
    const exch = turnover * (this.model.exchange_txn_bps / 10000.0);
    const stt = side === 'SELL' ? turnover * (this.model.stt_ctt_bps / 10000.0) : 0.0;
    const gst = (this.model.brokerage_per_order + exch) * this.model.gst_rate;
    const total = this.totalCost(fillPrice, qty, side);
    return {
      turnover: Number(turnover.toFixed(2)),
      brokerage: this.model.brokerage_per_order,
      exchange: Number(exch.toFixed(4)),
      stt: Number(stt.toFixed(4)),
      gst: Number(gst.toFixed(4)),
      total,
    };
  }
}

