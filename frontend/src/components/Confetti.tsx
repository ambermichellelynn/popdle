import { useEffect, useState } from "react";

interface ConfettiProps {
  active: boolean;
}

const COLORS = ["#538d4e", "#b59f3b", "#3a3a3c", "#aa3bff", "#c084fc"];
const PIECE_COUNT = 60;

interface Piece {
  id: number;
  left: number;
  delay: number;
  duration: number;
  color: string;
  rotation: number;
}

export function Confetti({ active }: ConfettiProps) {
  const [pieces, setPieces] = useState<Piece[] | null>(null);

  useEffect(() => {
    if (!active) return;
    const next = Array.from({ length: PIECE_COUNT }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 0.3,
      duration: 1.6 + Math.random() * 1.2,
      color: COLORS[i % COLORS.length],
      rotation: Math.random() * 360,
    }));
    setPieces(next);
    const timeout = setTimeout(() => setPieces(null), 2800);
    return () => clearTimeout(timeout);
  }, [active]);

  if (!pieces) return null;

  return (
    <div className="confetti-layer" aria-hidden="true">
      {pieces.map((p) => (
        <span
          key={p.id}
          className="confetti-piece"
          style={{
            left: `${p.left}%`,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
            backgroundColor: p.color,
            transform: `rotate(${p.rotation}deg)`,
          }}
        />
      ))}
    </div>
  );
}
