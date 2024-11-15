export const Alert = ({
  variant = "default",
  children,
  className = "",
  ...props
}) => (
  <div
    role="alert"
    className={`
        rounded-lg border p-4
        ${
          variant === "destructive"
            ? "border-destructive/50 text-destructive"
            : "border-border"
        }
        ${className}
      `}
    {...props}
  >
    {children}
  </div>
);
