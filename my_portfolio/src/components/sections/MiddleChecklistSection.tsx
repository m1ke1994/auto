import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { CheckCircle2 } from "lucide-react";
import { usePortfolioSection } from "@/lib/tracknode";

export function MiddleChecklistSection() {
  const content = usePortfolioSection<{
    title?: string;
    accent?: string;
    description?: string;
    items?: Array<{ text: string }>;
  }>("checklist");
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const checklistItems = content.items || [];

  return (
    <section className="section-padding bg-card/30">
      <div className="section-container" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="max-w-3xl mx-auto"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-center">
            {content.title} <span className="text-gold">{content.accent}</span>
          </h2>
          <p className="text-muted-foreground text-lg text-center mb-12">
            {content.description}
          </p>

          <div className="space-y-3">
            {checklistItems.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={isInView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.4, delay: 0.1 + index * 0.05 }}
                className="flex items-start gap-4 p-4 rounded-xl bg-background border border-border/50 hover:border-accent/30 transition-colors group"
              >
                <CheckCircle2 className="h-5 w-5 text-gold mt-0.5 flex-shrink-0 group-hover:scale-110 transition-transform" />
                <span className="text-foreground leading-relaxed">{item.text}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
