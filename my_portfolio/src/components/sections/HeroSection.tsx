import { motion } from "framer-motion";
import { ArrowDown, Briefcase, Code2, Wrench, UserCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { resolveMediaUrl, usePortfolioSection } from "@/lib/tracknode";

const badgeIcons = {
  briefcase: Briefcase,
  code: Code2,
  user: UserCheck,
  wrench: Wrench,
};

export function HeroSection() {
  const content = usePortfolioSection<{
    status_text?: string;
    title?: string;
    accent_title?: string;
    subtitle?: string;
    portrait_image?: string;
    portrait_alt?: string;
    primary_button_text?: string;
    primary_button_target?: string;
    secondary_button_text?: string;
    secondary_button_target?: string;
    badges?: Array<{ icon?: string; label: string }>;
  }>("hero");

  const scrollToTarget = (target = "#projects") => {
    document.querySelector(target)?.scrollIntoView({ behavior: "smooth" });
  };

  const badges = content.badges || [];
  const getBadgeIcon = (icon?: string) => badgeIcons[icon as keyof typeof badgeIcons] || Code2;
  const portraitImage = resolveMediaUrl(content.portrait_image);

  return (
    <section className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gold/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/5 rounded-full blur-3xl" />
      </div>

      <div className="section-container py-32 md:py-40">
        <div className="max-w-4xl mx-auto text-center">
          {portraitImage ? (
            <motion.img
              src={portraitImage}
              alt={content.portrait_alt || content.accent_title || "Portfolio portrait"}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="mx-auto mb-8 h-32 w-32 rounded-full border-4 border-background object-cover shadow-premium md:h-40 md:w-40"
            />
          ) : null}

          {/* Status badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20 text-sm font-medium text-accent mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            {content.status_text}
          </motion.div>

          {/* Main heading */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6"
          >
            {content.title}
            <br />
            <span className="text-gold">{content.accent_title}</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10"
          >
            {content.subtitle}
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Button
              size="lg"
              onClick={() => scrollToTarget(content.primary_button_target)}
              className="bg-foreground text-background hover:bg-foreground/90 px-8 h-12 text-base font-medium rounded-full"
            >
              {content.primary_button_text}
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => scrollToTarget(content.secondary_button_target)}
              className="border-2 px-8 h-12 text-base font-medium rounded-full hover:bg-accent/10 hover:border-accent"
            >
              {content.secondary_button_text}
            </Button>
          </motion.div>

          {/* Badges */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-wrap items-center justify-center gap-3"
          >
            {badges.map((badge, index) => {
              const Icon = getBadgeIcon(badge.icon);
              return (
              <motion.div
                key={badge.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: 0.5 + index * 0.1 }}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-card border border-border text-sm"
              >
                <Icon className="h-4 w-4 text-gold" />
                <span>{badge.label}</span>
              </motion.div>
              );
            })}
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
          >
            <ArrowDown className="h-6 w-6 text-muted-foreground" />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
