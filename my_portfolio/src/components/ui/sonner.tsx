import * as React from "react";
import { Toaster as SonnerToaster } from "sonner";

type SonnerProps = React.ComponentProps<typeof SonnerToaster>;

export function Toaster(props: SonnerProps) {
  return (
    <SonnerToaster
      position="top-right"
      richColors
      closeButton
      toastOptions={{
        classNames: {
          toast: "bg-background text-foreground border border-border shadow-md",
          description: "text-muted-foreground",
        },
      }}
      {...props}
    />
  );
}
