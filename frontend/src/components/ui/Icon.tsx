import { clsx } from 'clsx';

// Import commonly used icons
import {
  HomeIcon,
  CodeBracketIcon,
  ClockIcon,
  ChartBarIcon,
  UserIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  SunIcon,
  MoonIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XCircleIcon,
  EyeIcon,
  EyeSlashIcon,
  DocumentTextIcon,
  CloudArrowUpIcon,
  LinkIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlusIcon,
  MinusIcon,
  TrashIcon,
  PencilIcon,
  DocumentDuplicateIcon,
  ShareIcon,
  HeartIcon,
  StarIcon,
  BellIcon,
  EnvelopeIcon,
  PhoneIcon,
  MapPinIcon,
  CalendarIcon,
  ClipboardIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  ArrowPathIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
} from '@heroicons/react/24/outline';

import {
  HomeIcon as HomeIconSolid,
  CodeBracketIcon as CodeBracketIconSolid,
  ClockIcon as ClockIconSolid,
  ChartBarIcon as ChartBarIconSolid,
  UserIcon as UserIconSolid,
  Cog6ToothIcon as Cog6ToothIconSolid,
  CheckIcon as CheckIconSolid,
  ExclamationTriangleIcon as ExclamationTriangleIconSolid,
  InformationCircleIcon as InformationCircleIconSolid,
  XCircleIcon as XCircleIconSolid,
  HeartIcon as HeartIconSolid,
  StarIcon as StarIconSolid,
  BellIcon as BellIconSolid,
} from '@heroicons/react/24/solid';

const iconMap = {
  // Outline icons
  home: HomeIcon,
  'code-bracket': CodeBracketIcon,
  clock: ClockIcon,
  'chart-bar': ChartBarIcon,
  user: UserIcon,
  'cog-6-tooth': Cog6ToothIcon,
  'arrow-right-on-rectangle': ArrowRightOnRectangleIcon,
  'bars-3': Bars3Icon,
  'x-mark': XMarkIcon,
  sun: SunIcon,
  moon: MoonIcon,
  check: CheckIcon,
  'exclamation-triangle': ExclamationTriangleIcon,
  'information-circle': InformationCircleIcon,
  'x-circle': XCircleIcon,
  eye: EyeIcon,
  'eye-slash': EyeSlashIcon,
  'document-text': DocumentTextIcon,
  'cloud-arrow-up': CloudArrowUpIcon,
  link: LinkIcon,
  'magnifying-glass': MagnifyingGlassIcon,
  funnel: FunnelIcon,
  'chevron-down': ChevronDownIcon,
  'chevron-up': ChevronUpIcon,
  'chevron-left': ChevronLeftIcon,
  'chevron-right': ChevronRightIcon,
  plus: PlusIcon,
  minus: MinusIcon,
  trash: TrashIcon,
  pencil: PencilIcon,
  'document-duplicate': DocumentDuplicateIcon,
  share: ShareIcon,
  heart: HeartIcon,
  star: StarIcon,
  bell: BellIcon,
  envelope: EnvelopeIcon,
  phone: PhoneIcon,
  'map-pin': MapPinIcon,
  calendar: CalendarIcon,
  clipboard: ClipboardIcon,
  download: ArrowDownTrayIcon,
  upload: ArrowUpTrayIcon,
  refresh: ArrowPathIcon,
  play: PlayIcon,
  pause: PauseIcon,
  stop: StopIcon,

  // Solid icons
  'home-solid': HomeIconSolid,
  'code-bracket-solid': CodeBracketIconSolid,
  'clock-solid': ClockIconSolid,
  'chart-bar-solid': ChartBarIconSolid,
  'user-solid': UserIconSolid,
  'cog-6-tooth-solid': Cog6ToothIconSolid,
  'check-solid': CheckIconSolid,
  'exclamation-triangle-solid': ExclamationTriangleIconSolid,
  'information-circle-solid': InformationCircleIconSolid,
  'x-circle-solid': XCircleIconSolid,
  'heart-solid': HeartIconSolid,
  'star-solid': StarIconSolid,
  'bell-solid': BellIconSolid,
} as const;

export type IconName = keyof typeof iconMap;

interface IconProps {
  name: IconName;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  'aria-hidden'?: boolean;
}

const sizeClasses = {
  xs: 'h-3 w-3',
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
  xl: 'h-8 w-8',
};

export const Icon = ({
  name,
  size = 'md',
  className,
  'aria-hidden': ariaHidden = true,
  ...props
}) => {
  const IconComponent = iconMap[name];

  if (!IconComponent) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }

  return (
    <IconComponent
      className={clsx(sizeClasses[size], className)}
      aria-hidden={ariaHidden}
      {...props}
    />
  );
};