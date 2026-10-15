/**
 * Live commentary hooks for bulbul-build (Gully Bhaiya on Sarvam Bulbul).
 *
 * The game calls these at the moment things happen; they describe the ball,
 * the stroke and the result in plain words and hand them to
 * `window.bulbulCommentary.event(kind, detail, state)` if the page has one.
 * Without it they do nothing, so the game plays exactly as before.
 */
import { GAME, STYLES, SOLID_SHOT } from '../config/gameplay';
import { effectiveLine, stumpIntersection } from './DeliveryTrajectory';
import type { Delivery, ShotAttempt, ShotOutcome, ShotType } from './types';

type Hook = { event(kind: string, detail: Record<string, unknown>, state: Record<string, unknown>): void };
const hook = () => (window as unknown as { bulbulCommentary?: Hook }).bulbulCommentary;

function emit(kind: string, detail: Record<string, unknown>, state: Record<string, unknown>) {
  try { hook()?.event(kind, detail, state); } catch { /* commentary never breaks the game */ }
}

/** What the player physically did for the last stroke: a swipe and its direction, or keys. */
export interface RawInput { via: 'swipe' | 'keys'; direction: string; keys?: string; angle?: number }
let lastInput: RawInput | null = null;

const DIRECTIONS = ['up', 'up-right', 'right', 'down-right', 'down', 'down-left', 'left', 'up-left'];
/** A swipe as the player made it on the screen, before any left-hander mirroring. */
export function noteSwipe(dx: number, dy: number) {
  const angle = Math.round(Math.atan2(dx, -dy) * 180 / Math.PI);
  lastInput = { via: 'swipe', angle, direction: DIRECTIONS[((Math.round(angle / 45) % 8) + 8) % 8] };
}
const KEY_NAMES: Record<string, string> = { A: 'left', W: 'up', D: 'right', S: 'down' };
/** The keys as pressed (A/W/D/S, arrows read as the same), before any mirroring. */
export function noteKeys(keys: string[]) {
  lastInput = { via: 'keys', keys: keys.join('+'), direction: keys.map(k => KEY_NAMES[k] ?? k).join('+') };
}

const LENGTH: Partial<Record<Delivery['style'], string>> = {
  YORKER: 'yorker (at the toes)', SHORT: 'bouncer (short, chest high)', RIB: 'back of a length (rib high)',
};
const SPIN = new Set(['OFF_SPIN', 'LEG_SPIN', 'ARM_BALL']);

/** The ball, as a commentator would call it. */
export function describeBall(d: Delivery) {
  const turn = d.finalTargetX - d.baseTargetX;
  const spinner = SPIN.has(d.style);
  return {
    bowler: d.express ? 'express pace' : spinner ? 'spinner' : 'pace',
    type: STYLES[d.style].label.toLowerCase(),
    pace_kph: d.speedKph,
    length: LENGTH[d.style] ?? (d.style === 'SLOWER' ? 'slower ball, full' : 'good length'),
    line: effectiveLine(d).toLowerCase().replace('_', ' '),
    movement: Math.abs(turn) < 0.03 ? 'straight' : turn < 0 ? `${spinner ? 'turning' : 'swinging'} in to the batter` : `${spinner ? 'turning' : 'swinging'} away`,
    hitting_stumps: stumpIntersection(d),
  };
}

const STROKE: Record<ShotType, string> = {
  LEG: 'leg-side flick', LONG_ON: 'on drive to long-on', STRAIGHT: 'straight drive',
  COVER_LONG_OFF: 'cover drive', SQUARE_CUT: 'square cut', DEFEND: 'forward defence (block)',
  SCOOP: 'scoop', REVERSE_SCOOP: 'reverse scoop',
};
const WHERE: Record<ShotType, string> = {
  LEG: 'midwicket / square leg', LONG_ON: 'long-on', STRAIGHT: 'straight down the ground',
  COVER_LONG_OFF: 'cover / long-off', SQUARE_CUT: 'point', DEFEND: 'dead at his feet',
  SCOOP: 'over the keeper', REVERSE_SCOOP: 'over the slips',
};

function strokeName(shot: ShotType, d: Delivery, o: ShotOutcome) {
  if (o.advance) return 'charged down the pitch and lofted';
  if (o.swept) return 'slog sweep';
  if (o.sweptFlat) return 'sweep';
  if (o.squared) return 'square drive';
  if (shot === 'LEG' && (d.style === 'SHORT' || d.style === 'RIB')) return 'pull';
  if (shot === 'STRAIGHT' || shot === 'LONG_ON') return o.runs === 6 && !o.aerial ? `lofted ${STROKE[shot]}` : STROKE[shot];
  return STROKE[shot];
}

/** Where a ball that beat the bat ended up, when it got him out. */
function beaten(o: ShotOutcome) {
  return o.wicketType === 'BOWLED' ? ', into the stumps' : o.wicketType === 'LBW' ? ', onto the pad in front of the stumps' : '';
}

function result(o: ShotOutcome) {
  if (o.isWicket) {
    const how = o.wicketType === 'CAUGHT' ? (o.edged ? 'caught behind (edged)' : 'caught') : (o.wicketType ?? 'out').toLowerCase();
    return { out: true, how };
  }
  return { out: false, runs: o.runs };
}

/**
 * One ball, called the moment it is decided: at bat on ball, or as it passes
 * the bat. An aerial ball is decided here but only shown when it lands, so
 * `in_air` tells the commentator to build up first and give the result last.
 */
export function ballPlayed(d: Delivery, attempt: ShotAttempt | null, o: ShotOutcome, extra: {
  ball: string; meter: number | null; meterFull: boolean; specials: readonly string[]; call: string | null;
}, state: Record<string, unknown>) {
  const input = attempt ? lastInput : null;
  lastInput = null;
  const kind = o.isWicket ? 'wicket' : o.madeBatContact ? 'hit' : 'miss';
  // The game's sign is positive = late; Gully Bhaiya's protocol is positive = early.
  const delta = o.timingDeltaMs;
  const tight = !!STYLES[d.style].tight;
  const onTime = (tight ? GAME.timing.perfect * GAME.fastTimingScale : GAME.timing.perfect);
  const shot = attempt?.shotType ?? null;
  const detail: Record<string, unknown> = {
    ball: extra.ball,
    delivery: describeBall(d),
    swung: !!attempt,
    ...(input ? { input } : {}),
    ...(shot ? {
      shot: strokeName(shot, d, o),
      shot_code: shot,
      timing: o.timingGrade.toLowerCase(),
      timing_ms: delta === null ? null : -Math.round(delta),
      early_or_late: delta === null ? null : Math.abs(delta) <= onTime ? 'on time' : delta < 0 ? 'early' : 'late',
      suits_line: o.compatibility >= SOLID_SHOT,
      line_fit: Math.round(o.compatibility * 100) / 100,
      contact: o.edged ? 'edge' : !o.madeBatContact ? 'missed' : o.defended ? 'blocked' : o.aerial ? 'skied (top edge or mishit)' : o.timingGrade === 'PERFECT' ? 'middled' : o.timingGrade === 'GOOD' ? 'well timed' : 'got bat on it',
      went: o.madeBatContact ? (o.edged ? 'to the keeper' : WHERE[shot]) : `past the bat${beaten(o)}`,
    } : { shot: 'left alone', went: o.isWicket ? `nothing offered${beaten(o)}` : 'through to the keeper' }),
    ...result(o),
    in_air: o.aerial,
    ...(o.aerial ? { hang_ms: o.hangMs ?? GAME.aerialFlightMs } : {}),
    game_call: o.feedback,
    ...(extra.call ? { meter_call: extra.call } : {}),
    meter: extra.meter, meter_full: extra.meterFull,
    ...(extra.specials.length ? { special_ball_for: extra.specials.join(', ').toLowerCase() } : {}),
  };
  emit(kind, detail, state);
}

export function inningsStarted(detail: Record<string, unknown>, state: Record<string, unknown>) { lastInput = null; emit('start', detail, state); }
export function overDone(detail: Record<string, unknown>, state: Record<string, unknown>) { emit('over', detail, state); }
export function inningsEnded(detail: Record<string, unknown>, state: Record<string, unknown>) { emit('end', detail, state); }
/** The bowler has started his run-up: the highlight reel starts a clip here. */
export function ballComing() { emit('runup', {}, {}); }
