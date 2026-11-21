import React from "react";

// Personaggio originale in stile "Vice-city vibes": camicia hawaiana, occhiali a specchio,
// iced coffee e telefono. Camminata frontale lenta, ciclo di 45 frame (4 cicli = 180 frame).
const SKIN = "#c8875c";
const SKIN_DARK = "#a86a45";
const SHIRT = "#ff4f9a";
const SHORTS = "#e9dcc0";

export const Character: React.FC<{ frame: number; loop: number; stride: number }> = ({
  frame,
  loop,
  stride,
}) => {
  const p = (2 * Math.PI * frame) / stride;
  const L = (2 * Math.PI * frame) / loop;

  const liftA = Math.pow(Math.max(0, Math.sin(p)), 1.3);
  const liftB = Math.pow(Math.max(0, Math.sin(p + Math.PI)), 1.3);
  const sway = 7 * Math.sin(p);
  const bob = -7 * Math.abs(Math.sin(p)) + 3;
  const tilt = 1.6 * Math.sin(p);
  // sguardo: si guarda intorno una volta per loop
  const look = 14 * Math.sin(L) + 4 * Math.sin(2 * L);
  const headNod = 2.5 * Math.sin(2 * p);
  // riflesso sugli occhiali una volta per loop
  const glint = ((frame % loop) - 120) / 22;

  const leg = (hipX: number, lift: number, dir: number) => {
    const ankleY = 845 - 48 * lift;
    const ankleX = hipX + dir * 6;
    const kneeX = hipX + dir * (8 + 4 * lift);
    const kneeY = 680 - 18 * lift;
    const footScale = 1 + 0.07 * lift;
    return (
      <g>
        <path
          d={`M ${hipX} 520 Q ${kneeX} ${kneeY} ${ankleX} ${ankleY}`}
          stroke={SKIN}
          strokeWidth={50}
          fill="none"
          strokeLinecap="round"
        />
        {/* gamba degli shorts */}
        <path
          d={`M ${hipX} 515 L ${hipX + dir * 4} ${628 - 12 * lift}`}
          stroke={SHORTS}
          strokeWidth={72}
          strokeLinecap="butt"
        />
        {/* sneaker */}
        <g transform={`translate(${ankleX} ${ankleY + 18}) scale(${footScale})`}>
          <path d="M -30 -14 Q -32 14 -10 18 L 26 18 Q 40 16 36 0 Q 30 -16 14 -18 L -22 -20 Z" fill="#f6f6f2" />
          <rect x={-32} y={14} width={70} height={8} rx={4} fill="#2fd6d0" />
          <path d="M -18 -6 L 18 2" stroke="#ff4f9a" strokeWidth={5} strokeLinecap="round" />
        </g>
      </g>
    );
  };

  return (
    <svg viewBox="0 0 400 900" width="100%" height="100%" style={{ overflow: "visible" }}>
      <defs>
        <linearGradient id="lens" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffb347" />
          <stop offset="0.5" stopColor="#ff4f9a" />
          <stop offset="1" stopColor="#5b2bd1" />
        </linearGradient>
        <linearGradient id="shade" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#000" stopOpacity="0.25" />
          <stop offset="0.35" stopColor="#000" stopOpacity="0" />
          <stop offset="0.75" stopColor="#000" stopOpacity="0" />
          <stop offset="1" stopColor="#000" stopOpacity="0.3" />
        </linearGradient>
        <clipPath id="lensClip">
          <path d="M -58 -12 Q -56 -20 -6 -16 Q 0 14 -26 18 Q -54 18 -58 -12 Z M 58 -12 Q 56 -20 6 -16 Q 0 14 26 18 Q 54 18 58 -12 Z" />
        </clipPath>
      </defs>

      {/* ombra a terra */}
      <ellipse cx={200 + sway * 0.4} cy={868} rx={120 - 6 * Math.abs(Math.sin(p))} ry={16} fill="#000" opacity={0.45} />

      <g transform={`translate(${sway} ${bob})`}>
        {leg(172, liftA, -1)}
        {leg(228, liftB, 1)}

        <g transform={`rotate(${tilt} 200 500)`}>
          {/* braccio destro (lato spettatore) con iced coffee, oscilla */}
          <g transform={`rotate(${-6 * Math.sin(p)} 282 300)`}>
            <path d="M 282 300 Q 300 410 296 500" stroke={SKIN} strokeWidth={44} fill="none" strokeLinecap="round" />
            <path d="M 280 298 L 296 372" stroke={SHIRT} strokeWidth={54} strokeLinecap="round" />
            {/* bicchiere */}
            <g transform="translate(296 520)">
              <path d="M -24 -30 L 24 -30 L 19 40 L -19 40 Z" fill="#ffffff" opacity={0.35} />
              <path d="M -22 -10 L 22 -10 L 19 40 L -19 40 Z" fill="#7a4a2b" />
              <path d="M -22 -10 L 22 -10 L 21.4 0 L -21.4 0 Z" fill="#d9b48a" />
              <rect x={-27} y={-38} width={54} height={10} rx={4} fill="#f4f4f4" />
              <path d="M 6 -38 L 16 -82" stroke="#2fd6d0" strokeWidth={6} strokeLinecap="round" />
              <ellipse cx={0} cy={-2} rx={30} ry={20} fill={SKIN} />
            </g>
          </g>

          {/* busto: canotta + camicia aperta */}
          <path d="M 128 290 Q 200 268 272 290 L 262 520 Q 200 532 138 520 Z" fill="#fbfbf7" />
          <path d="M 120 288 Q 160 276 186 282 L 172 400 L 156 528 L 132 524 Q 116 400 120 288 Z" fill={SHIRT} />
          <path d="M 280 288 Q 240 276 214 282 L 228 400 L 244 528 L 268 524 Q 284 400 280 288 Z" fill={SHIRT} />
          {/* fiori della camicia */}
          {[
            [140, 330],
            [158, 430],
            [136, 490],
            [262, 340],
            [248, 450],
            [266, 500],
          ].map(([x, y], i) => (
            <g key={i} transform={`translate(${x} ${y}) rotate(${i * 40})`}>
              {[0, 72, 144, 216, 288].map((a) => (
                <ellipse key={a} cx={0} cy={-8} rx={5} ry={9} fill="#ffe066" transform={`rotate(${a})`} />
              ))}
              <circle r={4} fill="#ff8c42" />
            </g>
          ))}
          {/* collo e catenina */}
          <path d="M 180 230 L 180 288 Q 200 300 220 288 L 220 230 Z" fill={SKIN_DARK} />
          <path d="M 176 290 Q 200 330 224 290" stroke="#f2c94c" strokeWidth={4} fill="none" />
          {/* shorts */}
          <path d="M 136 505 L 264 505 L 268 560 L 136 560 Z" fill={SHORTS} />
          <rect x={136} y={503} width={128} height={12} fill="#c9b994" />
          <rect x={120} y={280} width={160} height={250} fill="url(#shade)" />

          {/* braccio sinistro (lato spettatore) con telefono davanti al petto */}
          <path d="M 118 300 Q 96 400 132 440 Q 160 452 186 412" stroke={SKIN} strokeWidth={44} fill="none" strokeLinecap="round" />
          <path d="M 120 298 L 106 372" stroke={SHIRT} strokeWidth={54} strokeLinecap="round" />
          <g transform={`translate(${190 + 2 * Math.sin(2 * p)} ${392}) rotate(${-12 + 3 * Math.sin(L * 3)})`}>
            <rect x={-26} y={-50} width={52} height={96} rx={10} fill="#1d1d26" />
            <rect x={-22} y={-46} width={44} height={88} rx={8} fill="#ff4f9a" />
            <circle cx={-10} cy={-32} r={7} fill="#1d1d26" />
            <circle cx={-10} cy={-14} r={7} fill="#1d1d26" />
            <ellipse cx={-4} cy={34} rx={22} ry={16} fill={SKIN} />
          </g>

          {/* testa */}
          <g transform={`translate(${look * 0.15} ${headNod}) rotate(${look * 0.08} 200 200)`}>
            <ellipse cx={132 + look * 0.1} cy={168} rx={12} ry={20} fill={SKIN_DARK} />
            <ellipse cx={268 + look * 0.1} cy={168} rx={12} ry={20} fill={SKIN_DARK} />
            <path d="M 136 120 Q 136 70 200 66 Q 264 70 264 120 L 262 190 Q 252 246 200 252 Q 148 246 138 190 Z" fill={SKIN} />
            {/* barba corta */}
            <path d="M 140 186 Q 150 246 200 252 Q 250 246 260 186 Q 240 232 200 234 Q 160 232 140 186 Z" fill="#3a2a22" opacity={0.55} />
            {/* capelli */}
            <path d="M 132 128 Q 128 52 204 46 Q 274 50 268 128 Q 262 96 236 88 Q 200 78 170 92 Q 142 100 132 128 Z" fill="#241913" />
            <path d="M 150 76 Q 210 30 262 84 Q 220 60 150 76 Z" fill="#3b2a1f" />
            {/* tratti del viso, si spostano con lo sguardo */}
            <g transform={`translate(${look} 0)`}>
              <path d={`M 200 156 Q 196 190 188 196 Q 200 202 210 196`} stroke={SKIN_DARK} strokeWidth={4} fill="none" strokeLinecap="round" />
              <path d="M 178 220 Q 202 228 222 214" stroke="#5a2c1f" strokeWidth={5} fill="none" strokeLinecap="round" />
              {/* occhiali a specchio */}
              <g transform="translate(200 150)">
                <path d="M -64 -14 L 64 -14" stroke="#e6c35c" strokeWidth={4} />
                <path d="M -58 -12 Q -56 -20 -6 -16 Q 0 14 -26 18 Q -54 18 -58 -12 Z" fill="url(#lens)" stroke="#e6c35c" strokeWidth={3} />
                <path d="M 58 -12 Q 56 -20 6 -16 Q 0 14 26 18 Q 54 18 58 -12 Z" fill="url(#lens)" stroke="#e6c35c" strokeWidth={3} />
                <g clipPath="url(#lensClip)">
                  <rect x={-90 + glint * 60} y={-30} width={14} height={60} fill="#fff" opacity={0.85} transform="skewX(-25)" />
                </g>
              </g>
            </g>
          </g>
        </g>
      </g>
    </svg>
  );
};
