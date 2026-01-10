import * as React from "react";

interface SwitchProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  id?: string;
}

export function Switch({ checked, onCheckedChange, id }: SwitchProps) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange(!checked)}
      onChange={() => onCheckedChange(!checked)}
      className={`relative inline-flex h-5 w-10 items-center rounded-full transition-colors duration-150 ${
        checked ? "bg-primary" : "bg-muted"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-150 ${
          checked ? "translate-x-5" : "translate-x-1"
        }`}
      />
    </button>
  );
}
