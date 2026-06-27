import { useState } from "react";
import { api } from "../api";

interface PaywallModalProps {
  userId: string;
  onClose: () => void;
  onLoggedIn: (userId: string) => void;
  mode?: "upgrade" | "account";
}

type Step = "auth" | "plan";
type AuthMode = "signup" | "login";

export function PaywallModal({ userId, onClose, onLoggedIn, mode = "upgrade" }: PaywallModalProps) {
  const [step, setStep] = useState<Step>("auth");
  const [authMode, setAuthMode] = useState<AuthMode>("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleAuthSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (authMode === "signup") {
        const user = await api.signup(userId, email, password);
        onLoggedIn(user.id);
      } else {
        const user = await api.login(email, password);
        onLoggedIn(user.id);
      }
      if (mode === "account") {
        onClose();
      } else {
        setStep("plan");
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCheckoutClick() {
    setError(null);
    setSubmitting(true);
    try {
      const session = await api.createCheckoutSession(userId);
      window.location.href = session.url;
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-x" onClick={onClose} aria-label="Close">
          ×
        </button>

        {step === "auth" ? (
          <>
            <div className="modal-header">
              <h2>{authMode === "signup" ? "Create your account" : "Log in"}</h2>
              <p className="modal-subtitle">
                {authMode === "signup"
                  ? mode === "account"
                    ? "Save your stats with an email and password."
                    : "Save your stats with an email and password before upgrading."
                  : "Log in to your Popdle account."}
              </p>
            </div>
            <form onSubmit={handleAuthSubmit} className="login-form">
              <input
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
              />
              <input
                type="password"
                required
                minLength={authMode === "signup" ? 8 : undefined}
                placeholder={authMode === "signup" ? "Password (min. 8 characters)" : "Password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              {error && <p className="error">{error}</p>}
              <button type="submit" className="primary-btn" disabled={submitting}>
                {authMode === "signup" ? "Create account" : "Log in"}
              </button>
            </form>
            <button
              className="ghost-btn"
              onClick={() => {
                setError(null);
                setAuthMode((m) => (m === "signup" ? "login" : "signup"));
              }}
            >
              {authMode === "signup" ? "Already have an account? Log in" : "Need an account? Sign up"}
            </button>
          </>
        ) : (
          <>
            <div className="modal-header">
              <h2>Upgrade to Premium</h2>
              <p className="modal-subtitle">See your stats and replay the puzzle archive.</p>
            </div>
            <div className="plan-compare">
              <div className="plan-col">
                <h3>Free</h3>
                <ul>
                  <li>Today's puzzle</li>
                </ul>
              </div>
              <div className="plan-col plan-col-premium">
                <h3>Premium</h3>
                <ul>
                  <li>Full stats &amp; history</li>
                  <li>20-day puzzle archive</li>
                </ul>
              </div>
            </div>

            <div className="test-card-note">
              <strong>This is Stripe test mode — no real charge.</strong>
              <p>
                Use card <code>4242 4242 4242 4242</code>, any future expiry, any 3-digit CVC, and
                any ZIP code.
              </p>
            </div>

            {error && <p className="error">{error}</p>}
            <button className="primary-btn" onClick={handleCheckoutClick} disabled={submitting}>
              Continue to checkout — $2.99/mo
            </button>
            <button className="ghost-btn" onClick={onClose}>
              Not now
            </button>
          </>
        )}
      </div>
    </div>
  );
}
