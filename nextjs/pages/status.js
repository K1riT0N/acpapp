// Open http://localhost:3000/status to check front-end -> API -> database.
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export default function Status() {
  const [state, setState] = useState({ kind: "checking", text: "Checking the connection..." });

  const check = () => {
    setState({ kind: "checking", text: "Checking the connection..." });
    api("/health")
      .then((d) => setState({ kind: "ok", text: `Connected. API: ${d.status}, database: ${d.database}.` }))
      .catch((e) => setState({ kind: "error", text: `Not connected. ${e.message}` }));
  };

  useEffect(check, []);

  return (
    <div className="panel" style={{ maxWidth: 480 }}>
      <h1>System check</h1>
      <p className="t-meta">Front-end → API → database</p>
      <p className={"mt " + (state.kind === "ok" ? "okbox" : state.kind === "error" ? "warnbox" : "note")} role="status">
        {state.text}
      </p>
      <button className="btn" onClick={check}>Check again</button>
    </div>
  );
}
