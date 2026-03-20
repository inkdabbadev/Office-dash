"use client"

import { useEffect, useState } from "react";

type Row = {
  id: number;
  channel_name: string;
  followers: number;
  posts: number;
  img_url: string;
  profile_url?: string;
  scraped_at?: string;
};

export default function Home() {
  const [rows, setRows] = useState<Row[]>([]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    async function fetchRows() {
      const res = await fetch("/api");
      const json = await res.json();
      setRows(json.data || []);
    }
    fetchRows();
    interval = setInterval(() => {
      fetchRows();
    }, 5000);

    return() => clearInterval(interval)

  },[]);

  const topTwo = rows.slice(0, 2);
  const rest = rows.slice(2);
  const maxFollowers = rows.length ? Math.max(...rows.map((r) => r.followers)) : 1;

  return (
    <div className="dashboard-root">
      {/* Grid overlay */}
      <div className="grid-overlay" />

      {/* Header */}
      <header className="dash-header">
        <div className="dash-title">
          <span className="title-badge">⬡</span>
          <h1>COMMAND <span className="title-accent">CENTER</span></h1>
          <span className="title-badge">⬡</span>
        </div>
        <div className="dash-subtitle">SOCIAL INTELLIGENCE DASHBOARD</div>
        <div className="live-indicator">
          <span className="live-dot" />
          LIVE
        </div>
      </header>

      {/* Top 2 Elite Cards */}
      <section className="elite-section">
        {topTwo.map((row, index) => (
          <div key={row.id} className={`elite-card rank-${index + 1}`}>
            <div className="elite-rank">#{index + 1}</div>
            <div className="elite-crown">{index === 0 ? "👑" : "⚡"}</div>

            <div className="elite-glow-ring">
              <div className="elite-avatar-wrap">
                <img src={row.img_url} alt="" className="elite-avatar" />
              </div>
            </div>

            <h2 className="elite-name">{row.channel_name}</h2>

            <div className="elite-stats">
              <div className="stat-block">
                <span className="stat-value">{row.followers.toLocaleString()}</span>
                <span className="stat-label">FOLLOWERS</span>
              </div>
              <div className="stat-divider" />
              <div className="stat-block">
                <span className="stat-value">{row.posts.toLocaleString()}</span>
                <span className="stat-label">POSTS</span>
              </div>
            </div>

            <div className="elite-bar">
              <div
                className="elite-bar-fill"
                style={{ width: `${Math.round((row.followers / maxFollowers) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </section>

      {/* Divider */}
      {rest.length > 0 && (
        <div className="section-divider">
          <div className="section-divider-line" />
          <span className="section-divider-label">ALL CHANNELS</span>
          <div className="section-divider-line" />
        </div>
      )}

      {/* Rest of channels — 2 rows, landscape cards */}
      <section className="grid-section">
        {[rest.slice(0, 4), rest.slice(4)].map((rowGroup, gi) => (
          <div key={gi} className="grid-row">
            {rowGroup.map((row) => (
              <div key={row.id} className="grid-card">
                <div className="grid-avatar-wrap">
                  <img src={row.img_url} alt="" className="grid-avatar" />
                </div>
                <div className="grid-info">
                  <h3 className="grid-name">{row.channel_name}</h3>
                  <div className="grid-stats-row">
                    <span className="grid-stat">
                      <span className="grid-stat-val">{row.followers.toLocaleString()}</span>
                      <span className="grid-stat-lbl"> FOLLOWERS</span>
                    </span>
                    <span className="grid-stat">
                      <span className="grid-stat-val">{row.posts.toLocaleString()}</span>
                      <span className="grid-stat-lbl"> POSTS</span>
                    </span>
                  </div>
                </div>
                <div className="grid-indicator" />
              </div>
            ))}
          </div>
        ))}
      </section>
    </div>
  );
}
