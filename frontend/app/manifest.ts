import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "AlgoTrade Sentinel",
    short_name: "AlgoTrade",
    description: "Algo trading research, monitoring, and paper portfolio platform.",
    start_url: "/",
    display: "standalone",
    background_color: "#020617",
    theme_color: "#06b6d4",
    icons: [
      {
        src: "/icons/icon-192x192.svg",
        sizes: "192x192",
        type: "image/svg+xml",
      },
      {
        src: "/icons/icon-512x512.svg",
        sizes: "512x512",
        type: "image/svg+xml",
        purpose: "maskable",
      },
    ],
  };
}
