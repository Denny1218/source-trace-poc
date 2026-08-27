import { useElapsedSeconds } from "../hooks/useElapsedSeconds";
import "./LongRunningTaskPanel.css";

interface LongRunningTaskPanelProps {
  active: boolean;
  title: string;
  description?: string;
}

export default function LongRunningTaskPanel({
  active,
  title,
  description,
}: LongRunningTaskPanelProps) {
  const elapsed = useElapsedSeconds(active);

  if (!active) return null;

  return (
    <div className="long-running-task-panel" role="status" aria-live="polite">
      <span className="long-running-spinner" aria-hidden="true" />
      <div className="long-running-text">
        <strong>{title}</strong>
        {description && <p>{description}</p>}
        <p className="long-running-elapsed">{elapsed}초 경과</p>
      </div>
    </div>
  );
}
