import { parse, isLosslessNumber, isSafeNumber, type LosslessNumber } from "lossless-json";

// Used for every forensics API response. Most numeric fields (block numbers,
// log indices, distance scores, funds_lost_usd) are safely representable as
// JS numbers and come back as plain numbers. Fields that exceed
// Number.MAX_SAFE_INTEGER — uint256 amounts inside log `args` (wad, amount,
// totalBalances, etc.) and internal-call `value_wei` — come back as exact
// decimal strings instead of being silently rounded by JSON.parse.
function reviveNumbers(_key: string, value: unknown): unknown {
  if (isLosslessNumber(value)) {
    const raw = (value as LosslessNumber).toString();
    return isSafeNumber(raw) ? Number(raw) : raw;
  }
  return value;
}

export function parseLosslessJSON<T>(text: string): T {
  return parse(text, reviveNumbers) as T;
}