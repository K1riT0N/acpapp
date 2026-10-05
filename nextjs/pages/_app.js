// Wraps every page: login state, toasts, header and footer, like the prototype's render().
import Head from "next/head";

import Footer from "@/components/Footer";
import Header from "@/components/Header";
import { ToastProvider } from "@/components/Toasts";
import { AuthProvider } from "@/lib/auth";
import "@/styles/globals.css";

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <ToastProvider>
        <Head>
          <title>Nadd: bookings for local shops</title>
          <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        </Head>
        <Header />
        <main className="wrap" id="main">
          <Component {...pageProps} />
        </main>
        <Footer />
      </ToastProvider>
    </AuthProvider>
  );
}
