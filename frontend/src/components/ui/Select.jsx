export const Select = ({
  label,
  value,
  onChange,
  options,
  disabled,
  className = "",
}) => (
  <div className="space-y-2">
    {label && <label className="text-sm font-medium">{label}</label>}
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={`
          w-full rounded-md border border-input bg-background px-3 py-2
          text-sm ring-offset-background
          focus:outline-none focus:ring-2 focus:ring-ring
          disabled:cursor-not-allowed disabled:opacity-50
          ${className}
        `}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  </div>
);
