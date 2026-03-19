interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  color?: "blue" | "green" | "purple" | "orange";
}

const colorMap = {
  blue: "border-blue-500 bg-blue-50",
  green: "border-green-500 bg-green-50",
  purple: "border-purple-500 bg-purple-50",
  orange: "border-orange-500 bg-orange-50",
};

const textColorMap = {
  blue: "text-blue-700",
  green: "text-green-700",
  purple: "text-purple-700",
  orange: "text-orange-700",
};

export default function MetricCard({
  title,
  value,
  subtitle,
  icon,
  color = "blue",
}: MetricCardProps) {
  return (
    <div
      className={`rounded-lg border-l-4 p-5 shadow-sm bg-white ${colorMap[color]}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {title}
          </p>
          <p className={`mt-1 text-3xl font-bold ${textColorMap[color]}`}>
            {value}
          </p>
          {subtitle && (
            <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
          )}
        </div>
        {icon && (
          <span className="text-2xl opacity-70">{icon}</span>
        )}
      </div>
    </div>
  );
}
