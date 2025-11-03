import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import * as React from "react"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "terminal-text inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm border-2 border-border bg-[hsl(var(--surface))] text-[hsl(var(--foreground))] text-[0.625rem] font-semibold uppercase tracking-[0.32em] shadow-[var(--shadow-sm)] transition-all duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--accent))] focus-visible:ring-offset-2 focus-visible:ring-offset-[hsl(var(--surface))] disabled:pointer-events-none disabled:opacity-40 hover:-translate-y-[1px] hover:bg-[hsl(var(--surface-hover))] hover:shadow-[var(--shadow-md)] active:translate-y-0 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))] shadow-[var(--shadow-md)] hover:brightness-110",
        destructive:
          "bg-[hsl(var(--destructive))] text-[hsl(var(--destructive-foreground))] hover:brightness-110",
        outline:
          "bg-[hsl(var(--surface))] text-[hsl(var(--foreground))]",
        secondary:
          "bg-[hsl(var(--surface-elevated))] text-[hsl(var(--foreground))]",
        ghost:
          "border-transparent bg-transparent text-[hsl(var(--foreground))] shadow-none hover:border-border",
        link:
          "border-0 bg-transparent shadow-none normal-case tracking-normal text-[hsl(var(--accent))] underline underline-offset-4 hover:no-underline",
      },
      size: {
        default: "px-4 py-2 min-h-[2.25rem]",
        sm: "px-3 py-1.5 text-[0.55rem] min-h-[1.75rem]",
        lg: "px-6 py-3 text-[0.75rem] min-h-[2.75rem]",
        icon: "px-0 h-8 w-8 text-[0.55rem]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
