import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { resolveMediaUrl, usePortfolioSection } from "@/lib/tracknode";

export function AboutSection() {
  const content = usePortfolioSection<{
    title?: string;
    accent?: string;
    paragraphs?: Array<{ text: string }>;
    profile_image?: string;
    profile_image_alt?: string;
  }>("about");
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const profileImage = resolveMediaUrl(content.profile_image);

  return (
    <section id="about" className="section-padding bg-card/30">
      <div className="section-container" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="max-w-3xl mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            {content.title} <span className="text-gold">{content.accent}</span>
          </h2>
          <div className="grid gap-8 md:grid-cols-[minmax(0,1fr)_220px] md:items-start">
            <div className="space-y-4 text-muted-foreground text-lg leading-relaxed">
              {(content.paragraphs || []).map((paragraph) => (
                <p key={paragraph.text}>{paragraph.text}</p>
              ))}
            </div>
            {profileImage ? (
              <img
                src={profileImage}
                alt={content.profile_image_alt || content.title || "About"}
                className="w-full max-w-[220px] rounded-2xl border border-border object-cover shadow-premium"
              />
            ) : null}
          </div>
        </motion.div>

      </div>
    </section>
  );
}
