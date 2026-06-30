import { Link, useLocation } from "wouter";
import { Brain, MessageSquare, LayoutGrid, Info } from "lucide-react";
import { cn } from "@/lib/utils";

export function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  const navItems = [
    { href: "/", label: "Home", icon: Brain },
    { href: "/chat", label: "Chat", icon: MessageSquare },
    { href: "/topics", label: "Topics", icon: LayoutGrid },
    { href: "/about", label: "About", icon: Info },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2" data-testid="link-home">
            <Brain className="w-8 h-8 text-primary" />
            <span className="font-serif text-xl font-bold tracking-tight text-primary">Neuroguide AI</span>
          </Link>
          
          <nav className="flex items-center gap-6">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location === item.href;
              return (
                <Link 
                  key={item.href} 
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary",
                    isActive ? "text-primary" : "text-muted-foreground"
                  )}
                  data-testid={`link-${item.label.toLowerCase()}`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      
      <main className="flex-1 flex flex-col">
        {children}
      </main>
    </div>
  );
}
