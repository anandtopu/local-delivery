interface StatusBadgeProps {
  status: string;
}

const STATUS_STYLES: Record<string, string> = {
  CONFIRMED: "bg-green-100 text-green-800",
  IN_TRANSIT: "bg-blue-100 text-blue-800",
  DELIVERED: "bg-slate-100 text-slate-600",
  CANCELLED: "bg-red-100 text-red-700",
  // Cache status
  HIT: "bg-green-100 text-green-800",
  MISS: "bg-yellow-100 text-yellow-800",
  PARTIAL: "bg-orange-100 text-orange-800",
};

const STATUS_LABELS: Record<string, string> = {
  CONFIRMED: "Confirmed",
  IN_TRANSIT: "In Transit",
  DELIVERED: "Delivered",
  CANCELLED: "Cancelled",
  HIT: "Cache HIT",
  MISS: "Cache MISS",
  PARTIAL: "Cache PARTIAL",
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] ?? "bg-slate-100 text-slate-600";
  const label = STATUS_LABELS[status] ?? status;

  return (
    <span className={`badge ${style}`}>
      {label}
    </span>
  );
}
