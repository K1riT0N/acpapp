// Wrap a page that needs a logged-in customer or shop owner:
//   <RequireRole role="shop_owner" message="Log in to manage your shop.">...page...</RequireRole>
// The API checks the role again on every request; this only decides what the page shows.
import { useAuth } from "@/lib/auth";
import { Loading, LoginPrompt, NotFor } from "@/components/States";

export default function RequireRole({ role, message, children }) {
  const { user, ready } = useAuth();
  if (!ready) return <Loading />;
  if (!user) return <LoginPrompt message={message} />;
  if (role && user.role !== role) return <NotFor role={role} />;
  return children;
}
