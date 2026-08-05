import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Zap, Code2, Users, Shield, Target, Bug, Layout } from "lucide-react";
import { resolveMediaUrl, usePortfolioSection } from "@/lib/tracknode";

const reasonIcons = {
  bug: Bug,
  code: Code2,
  layout: Layout,
  shield: Shield,
  target: Target,
  users: Users,
  zap: Zap,
};

export function WhyMeSection() {
  const content = usePortfolioSection<{
    title?: string;
    accent?: string;
    description?: string;
    illustration_image?: string;
    illustration_alt?: string;
    reasons?: Array<{ icon?: string; image?: string; image_alt?: string; text: string }>;
  }>("why-me");
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const reasons = content.reasons || [];
  const getReasonIcon = (icon?: string) => reasonIcons[icon as keyof typeof reasonIcons] || Code2;
  const sectionImage = resolveMediaUrl(content.illustration_image);

  return (
    <section className="section-padding">
      <div className="section-container" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-center">
            {content.title} <span className="text-gold">{content.accent}</span>
          </h2>
          <p className="text-muted-foreground text-lg text-center mb-12 max-w-2xl mx-auto">
            {content.description}
          </p>
          {sectionImage ? (
            <img
              src={sectionImage}
              alt={content.illustration_alt || content.title || "Why me"}
              className="mb-10 h-56 w-full rounded-2xl border border-border object-cover shadow-premium"
            />
          ) : null}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {reasons.map((reason, index) => {
              const Icon = getReasonIcon(reason.icon);
              const reasonImage = resolveMediaUrl(reason.image);
              return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                animate={isInView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.4, delay: 0.1 + index * 0.05 }}
                className="flex items-start gap-4 p-4 rounded-xl bg-card border border-border/50 hover:border-accent/30 transition-colors"
              >
                {reasonImage ? (
                  <img src={reasonImage} alt={reason.image_alt || ""} className="h-10 w-10 flex-shrink-0 rounded-lg object-cover" />
                ) : (
                  <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                    <Icon className="h-5 w-5 text-gold" />
                  </div>
                )}
                <p className="text-foreground leading-relaxed pt-2">{reason.text}</p>
              </motion.div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
