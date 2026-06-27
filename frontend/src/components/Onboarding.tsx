import { useEffect, useState } from "react";
import { api } from "../api";

interface OnboardingProps {
  userId: string;
  onDone: () => void;
}

export function Onboarding({ userId, onDone }: OnboardingProps) {
  const [variant, setVariant] = useState<string | null>(null);

  useEffect(() => {
    api
      .getAssignment(userId, "onboarding_flow")
      .then((res) => setVariant(res.variant))
      .catch(() => setVariant("control"));
  }, [userId]);

  if (!variant) return null;

  return (
    <div className="onboarding">
      <h1>Popdle</h1>
      <p>Guess the pop-culture word — movies, shows, and actors, one a day.</p>

      {variant === "guided_tutorial" && (
        <ol className="tutorial-steps">
          <li>Each day has a new word from a movie, TV show, or actor's name.</li>
          <li>Green = right letter, right spot. Yellow = right letter, wrong spot.</li>
          <li>You get 6 guesses. Build your streak by playing every day.</li>
        </ol>
      )}

      <button onClick={onDone}>Play today's puzzle</button>
    </div>
  );
}
