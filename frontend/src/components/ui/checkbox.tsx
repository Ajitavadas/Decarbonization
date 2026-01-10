import * as React from "react";

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  label?: string;
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className = "", label, checked, onCheckedChange, ...props }, ref) => {
    return (
      <label className={`inline-flex items-center space-x-2 cursor-pointer ${className}`}>
        <input
          type="checkbox"
          ref={ref}
          className="h-4 w-4 rounded border border-input text-primary focus:ring-primary"
          checked={checked}
          onChange={(e) => onCheckedChange?.(e.target.checked)}
          {...props}
        />
        {label ? <span className="text-sm text-foreground">{label}</span> : null}
      </label>
    );
  }
);

Checkbox.displayName = "Checkbox";
