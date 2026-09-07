import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white px-6 text-center">
      <h2 className="text-6xl font-heading text-[#0F172A] tracking-wider mb-4">
        404 — PAGE NOT FOUND
      </h2>
      <p className="text-gray-600 mb-8 max-w-md font-body">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link
        href="/"
        className="px-6 py-3 rounded-lg bg-brand-600 text-white font-medium hover:bg-brand-700 transition"
      >
        Return to Home
      </Link>
    </div>
  );
}
