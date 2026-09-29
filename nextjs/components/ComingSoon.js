// Temporary page for links that point at pages from later build steps, so they don't show a 404.
import Link from "next/link";

import RequireRole from "@/components/RequireRole";

export default function ComingSoon({ title, step, role, message = "Log in to see this page." }) {
  const body = (
    <div className="empty-state">
      <h1>{title}</h1>
      <p className="lede">This page is added in step {step} of the build plan.</p>
      <Link className="btn" href={role === "shop_owner" ? "/owner/services" : "/"}>
        {role === "shop_owner" ? "Go to Services" : "Back to all shops"}
      </Link>
    </div>
  );
  return role !== undefined ? <RequireRole role={role} message={message}>{body}</RequireRole> : body;
}
