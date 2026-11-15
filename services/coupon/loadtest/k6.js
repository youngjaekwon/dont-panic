import grpc from 'k6/net/grpc';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const GRPC_ADDR = __ENV.GRPC_ADDR || 'app:50051';
const TOTAL = parseInt(__ENV.TOTAL || '1000');
const RATE = parseInt(__ENV.RATE || '10000');
const START_DELAY = parseFloat(__ENV.START_DELAY || '3');
const DURATION = __ENV.DURATION || '10s';

const issued = new Counter('issued');
const notStarted = new Counter('not_started');
const soldOut = new Counter('sold_out');
const unexpected = new Counter('unexpected');

export const options = {
  scenarios: {
    burst: {
      executor: 'constant-arrival-rate',
      rate: RATE,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: Math.min(RATE, 1000),
      maxVUs: 3000,
    },
  },
  thresholds: {
    issued: [`count==${TOTAL}`],
    unexpected: ['count==0'],
    checks: ['rate==1'],
  },
  summaryTrendStats: ['avg', 'p(50)', 'p(95)', 'p(99)', 'max'],
};

const client = new grpc.Client();
client.loadProtoset('/gen/descriptor.binpb');
const SVC = 'coupon.v1.CouponService/';

function call(method, req) {
  const res = client.invoke(SVC + method, req);
  const kind = { [grpc.StatusOK]: 'ok', [grpc.StatusFailedPrecondition]: 'not_started', [grpc.StatusResourceExhausted]: 'sold_out' }[res.status];
  return { kind: kind || `grpc ${res.status}`, body: res.message };
}

function connect() {
  client.connect(GRPC_ADDR, { plaintext: true });
}

export function setup() {
  connect();
  unexpected.add(0);
  const startsAt = new Date(Date.now() + START_DELAY * 1000).toISOString();
  const res = call('CreateCampaign', { name: 'loadtest', total_quantity: TOTAL, starts_at: startsAt });
  if (res.kind !== 'ok') throw new Error(`campaign create failed: ${res.kind}`);
  console.log(`campaign ${res.body.id}, starts_at ${startsAt}`);
  return { id: res.body.id };
}

export default function (data) {
  if (__ITER === 0) connect();
  const res = call('IssueCoupon', { campaign_id: data.id });
  ({ ok: issued, not_started: notStarted, sold_out: soldOut }[res.kind] || unexpected).add(1);
  if (!['ok', 'not_started', 'sold_out'].includes(res.kind)) console.warn(res.kind);
}

export function teardown(data) {
  connect();
  const c = call('GetCampaign', { campaign_id: data.id }).body;
  const coupons = [];
  let token = '';
  do {
    const page = call('ListCoupons', { campaign_id: data.id, page_size: 1000, page_token: token }).body;
    coupons.push(...(page.coupons || []));
    token = page.next_page_token ?? page.nextPageToken ?? '';
  } while (token);
  const ms = (s) => Date.parse(s.replace(/(\.\d{3})\d+/, '$1'));
  const startsAt = ms(c.starts_at || c.startsAt);
  const issuedCount = c.issued_count ?? c.issuedCount;
  check(c, {
    'issued in PG == TOTAL': () => coupons.length === TOTAL && issuedCount === TOTAL,
    'no duplicate codes': () => new Set(coupons.map((x) => x.code)).size === coupons.length,
    'nothing issued before starts_at': () => coupons.every((x) => ms(x.issued_at || x.issuedAt) >= startsAt),
  });
}
