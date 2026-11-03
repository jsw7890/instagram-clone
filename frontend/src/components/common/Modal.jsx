export default function Modal({ title, onClose, children, wide }) {
  return (
    <div className="modal-back" onClick={onClose} role="dialog">
      <div className="modal" style={wide ? { width: 900 } : undefined} onClick={(e) => e.stopPropagation()}>
        {title && <h3>{title}</h3>}
        {children}
      </div>
    </div>
  );
}
