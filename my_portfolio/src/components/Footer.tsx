import { Github, Send, Mail, Instagram } from "lucide-react";

const socialLinks = [
  { icon: Github, href: "https://github.com", label: "GitHub" },
  { icon: Send, href: "https://t.me/username", label: "Telegram" },
  { icon: Mail, href: "mailto:dev@example.com", label: "Email" },
  { icon: Instagram, href: "https://instagram.com/username", label: "Instagram" },
];

const navLinks = [
  { label: "Обо мне", href: "#about" },
  { label: "Навыки", href: "#skills" },
  { label: "Проекты", href: "#projects" },
  { label: "Контакты", href: "#contact" },
];

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-card/50">
      <div className="section-container py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
          {/* Brand */}
          <div>
            <a href="#" className="font-display font-bold text-xl tracking-tight inline-block mb-4">
              <span className="text-gold">{"<"}</span>
              Alexandr_Tishechkin
              <span className="text-gold">{" />"}</span>
            </a>
            <p className="text-muted-foreground text-sm max-w-xs">
              Middle Fullstack разработчик. Создаю веб-приложения на Vue.js и Django.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="font-display font-semibold mb-4">Навигация</h4>
            <ul className="space-y-2">
              {navLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground transition-colors text-sm"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Social */}
          <div>
            <h4 className="font-display font-semibold mb-4">Связаться</h4>
            <div className="flex items-center gap-3">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/10 transition-all"
                  aria-label={social.label}
                >
                  <social.icon className="h-5 w-5" />
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-12 pt-8 border-t border-border text-center">
          <p className="text-muted-foreground text-sm">
            © {currentYear} Все права защищены. Разработано с{" "}
            <span className="text-gold">♥</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
