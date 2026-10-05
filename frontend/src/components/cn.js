// Merge class names, skipping falsy values.
export function cn(...args) {
  return args.filter(Boolean).join(' ');
}