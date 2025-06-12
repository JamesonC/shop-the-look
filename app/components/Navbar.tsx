// components/Navbar.tsx
import React from 'react';
import Link from 'next/link';

const Navbar: React.FC = () => {
  return (
    <nav className="w-full bg-white border-b border-gray-200">
      {/* container: centers content, full width on small screens, max width on large */}
      <div className="container mx-auto flex items-center justify-between px-4 py-3">
        {/* logo + title */}
        <Link href="/" className="flex items-center gap-2 text-gray-900 hover:opacity-80">
          <svg
            className="h-6 w-6 flex-shrink-0"
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* …icon paths… */}
          </svg>
          <span className="text-lg font-semibold">🧦 Sock Scout</span>
        </Link>

        {/* feedback button stays right */}
        <button
          type="button"
          onClick={() => window.open('https://forms.gle/4jk3KpF7vJ41efph6', '_blank')}
          className="ml-auto rounded-full bg-red-600 px-4 py-2 text-sm font-bold text-white transition hover:bg-red-700"
        >
          Feedback
        </button>
      </div>
    </nav>
  );
};

export default Navbar;