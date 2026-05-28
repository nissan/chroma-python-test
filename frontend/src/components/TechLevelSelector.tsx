import { type TechLevel } from '@/lib/api'

interface Props {
  value: TechLevel
  onChange: (level: TechLevel) => void
}

const LEVELS: { value: TechLevel; label: string; description: string }[] = [
  { value: 'junior', label: 'Junior', description: 'Plain English, analogies' },
  { value: 'mid', label: 'Mid', description: 'Concepts with examples' },
  { value: 'deep', label: 'Deep', description: 'Implementation details' },
]

export function TechLevelSelector({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs text-muted-foreground">Level:</span>
      <div className="flex rounded-md border overflow-hidden">
        {LEVELS.map((level) => (
          <button
            key={level.value}
            title={level.description}
            onClick={() => onChange(level.value)}
            className={[
              'px-2.5 py-1 text-xs transition-colors',
              value === level.value
                ? 'bg-primary text-primary-foreground'
                : 'bg-background text-muted-foreground hover:bg-muted',
            ].join(' ')}
          >
            {level.label}
          </button>
        ))}
      </div>
    </div>
  )
}
