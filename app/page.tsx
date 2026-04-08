interface OsSummary {
  id: number;
  created_at: string;
  phase: string;
  active_agents: number;
  approval_rate: number | null;
  approved_count: number | null;
  rejected_count: number | null;
  co_degeneration_alert: boolean;
  raw_metadata: Record<string, unknown> | null;
}

interface ObsRow {
  agent_name: string;
  execution_status: "success" | "failure" | "skipped";
  output_count: number;
  executed_at: string;
}

async function getOsSummary(): Promise<OsSummary | null> {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  try {
    const res = await fetch(
      `${url}/rest/v1/os_summary?select=*&order=created_at.desc&limit=1`,
      {
        headers: { apikey: key, Authorization: `Bearer ${key}` },
        next: { revalidate: 300 },
      }
    );
    const data: OsSummary[] = await res.json();
    return data[0] ?? null;
  } catch {
    return null;
  }
}

async function getObsRows(): Promise<ObsRow[]> {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_ANON_KEY;
  if (!url || !key) return [];
  try {
    const res = await fetch(
      `${url}/rest/v1/agent_observability?select=agent_name,execution_status,output_count,executed_at&order=executed_at.desc&limit=20`,
      {
        headers: { apikey: key, Authorization: `Bearer ${key}` },
        next: { revalidate: 60 },
      }
    );
    return (await res.json()) ?? [];
  } catch {
    return [];
  }
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    success: "bg-green-800 text-green-100",
    failure: "bg-red-800 text-red-100",
    skipped: "bg-yellow-800 text-yellow-100",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-mono ${colors[status] ?? "bg-gray-700 text-gray-100"}`}
    >
      {status}
    </span>
  );
}

export default async function DashboardPage() {
  const [summary, obsRows] = await Promise.all([getOsSummary(), getObsRows()]);
  const phase = summary?.phase ?? process.env.YOHAKU_OS_PHASE ?? "Phase 3";
  const activeAgents = summary?.active_agents ?? 19;
  const approvalRate = summary?.approval_rate;
  const coDegenAlert = summary?.co_degeneration_alert ?? false;
  const failureCount = obsRows.filter((r) => r.execution_status === "failure").length;

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-8">
        <h1 className="text-2xl font-bold tracking-tight">YOHAKU OS Dashboard</h1>
        <div className="flex flex-wrap gap-2 text-sm items-center">
          <span className="bg-blue-900 border border-blue-700 text-blue-200 px-3 py-1 rounded-full text-sm font-medium">
            {phase}
          </span>
          <span className="bg-gray-800 px-3 py-1 rounded-full">
            稼働 {activeAgents} Agents
          </span>
          {approvalRate !== null && approvalRate !== undefined && (
            <span className="bg-gray-800 px-3 py-1 rounded-full">
              承認率 {Math.round(approvalRate * 100)}%
            </span>
          )}
          {coDegenAlert && (
            <span className="bg-orange-900 border border-orange-700 px-3 py-1 rounded-full text-orange-200">
              ⚠️ 共退化アラート
            </span>
          )}
          {failureCount > 0 && (
            <span className="bg-red-900 border border-red-700 px-3 py-1 rounded-full text-red-200">
              🔴 障害 {failureCount}
            </span>
          )}
        </div>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-8">
        {/* OS Summary */}
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h2 className="text-gray-400 text-xs uppercase tracking-wider mb-4">
            OS 状態サマリー
          </h2>
          {summary ? (
            <dl className="space-y-2 text-sm">
              {(
                [
                  ["Phase", summary.phase],
                  ["稼働Agent数", summary.active_agents],
                  [
                    "承認率",
                    approvalRate != null
                      ? `${Math.round(approvalRate * 100)}%`
                      : "—",
                  ],
                  ["承認件数", summary.approved_count ?? "—"],
                  ["却下件数", summary.rejected_count ?? "—"],
                  ["共退化アラート", coDegenAlert ? "🔴 あり" : "🟢 なし"],
                  [
                    "最終更新",
                    new Date(summary.created_at).toLocaleString("ja-JP", {
                      timeZone: "Asia/Tokyo",
                    }),
                  ],
                ] as [string, string | number][]
              ).map(([label, value]) => (
                <div key={label} className="flex justify-between">
                  <dt className="text-gray-500">{label}</dt>
                  <dd className="text-gray-200 font-mono">{String(value)}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-gray-600 text-sm">
              データなし — Supabase 未接続または初回実行前
            </p>
          )}
        </div>

        {/* Agent Observability */}
        <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
          <h2 className="text-gray-400 text-xs uppercase tracking-wider mb-4">
            直近実行ログ（最新20件）
          </h2>
          {obsRows.length > 0 ? (
            <div className="space-y-1.5 overflow-y-auto max-h-72">
              {obsRows.map((row, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-sm py-0.5"
                >
                  <span className="font-mono text-gray-300 truncate max-w-[40%]">
                    {row.agent_name}
                  </span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-gray-600 text-xs hidden sm:inline">
                      {new Date(row.executed_at).toLocaleString("ja-JP", {
                        timeZone: "Asia/Tokyo",
                        month: "2-digit",
                        day: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    <StatusBadge status={row.execution_status} />
                    <span className="text-gray-500 text-xs w-8 text-right">
                      +{row.output_count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 text-sm">
              データなし — agent_observability テーブル未作成
            </p>
          )}
        </div>
      </div>

      {/* Footer */}
      <p className="text-center text-gray-700 text-xs">
        YOHAKU Civilization OS v2.1 — Phase A Next.js Foundation
      </p>
    </main>
  );
}
