// Type declarations for JSX files
declare module '*.jsx' {
  import { ComponentType } from 'react';
  const component: ComponentType<any>;
  export default component;
}

declare module '*.js' {
  const content: any;
  export default content;
}
