interface PaywallModalProps {
  onClose: () => void;
  onUpgrade: () => void;
}

export function PaywallModal({ onClose, onUpgrade }: PaywallModalProps) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Go Premium</h2>
        <ul>
          <li>Full stats history & streak insurance</li>
          <li>Unlimited hints</li>
          <li>Archive of past daily puzzles</li>
        </ul>
        <button className="upgrade-btn" onClick={onUpgrade}>
          Upgrade — $2.99/mo
        </button>
        <button className="close-btn" onClick={onClose}>
          Not now
        </button>
      </div>
    </div>
  );
}
