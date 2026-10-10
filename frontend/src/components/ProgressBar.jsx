export default function ProgressBar({ percent, label }) {
  return (
    <>
      <div className="bar" role="progressbar" aria-valuenow={percent} aria-valuemin="0" aria-valuemax="100">
        <span style={{ width: `${percent}%` }} />
      </div>
      {label && (
        <div className="bar-label">
          <span>{label}</span>
          <span>{percent}%</span>
        </div>
      )}
    </>
  );
}
