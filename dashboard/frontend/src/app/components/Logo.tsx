export function Logo({ size = 32 }: { size?: number }) {
  const s = size;
  return (
    <svg width={s} height={s} viewBox="0 0 32 32" fill="none">
      <defs>
        <style>{`
          @keyframes logo-spin-cw { to { transform: rotate(360deg); } }
          @keyframes logo-spin-ccw { to { transform: rotate(-360deg); } }
          @keyframes logo-pulse {
            0%, 100% { opacity: 0.4; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.3); }
          }
          .logo-outer { animation: logo-spin-cw 12s linear infinite; transform-origin: 16px 16px; }
          .logo-inner { animation: logo-spin-ccw 20s linear infinite; transform-origin: 16px 16px; }
          .logo-dot { animation: logo-pulse 2s ease-in-out infinite; transform-origin: 16px 16px; }
        `}</style>
      </defs>
      <polygon
        className="logo-outer"
        points="16,2 28,9 28,23 16,30 4,23 4,9"
        stroke="#00f5ff"
        strokeWidth="1.5"
        strokeOpacity="0.7"
        fill="none"
      />
      <polygon
        className="logo-inner"
        points="16,6 24,10 24,22 16,26 8,22 8,10"
        stroke="#00f5ff"
        strokeWidth="1"
        strokeOpacity="0.3"
        fill="none"
      />
      <path
        d="M12 12h8M12 12v8M12 20h6"
        stroke="#00f5ff"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle
        className="logo-dot"
        cx="16"
        cy="16"
        r="1.5"
        fill="#00f5ff"
      />
    </svg>
  );
}
