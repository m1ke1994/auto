import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { BookOpen, Code2, Server, Wrench } from "lucide-react";
import { normalizeStringList, resolveMediaUrl, usePortfolioSection } from "@/lib/tracknode";

const skillIcons = {
  book: BookOpen,
  code: Code2,
  server: Server,
  wrench: Wrench,
};

export function SkillsSection() {
  const content = usePortfolioSection<{
    title?: string;
    accent?: string;
    description?: string;
    illustration_image?: string;
    illustration_alt?: string;
    groups?: Array<{ id: string; title: string; icon?: string; image?: string; image_alt?: string; skills: unknown[] }>;
  }>("skills");
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const skillGroups = content.groups || [];
  const getSkillIcon = (icon?: string) => skillIcons[icon as keyof typeof skillIcons] || Code2;
  const sectionImage = resolveMediaUrl(content.illustration_image);

  return (
    <section id="skills" className="section-padding">
      <div className="section-container" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            {content.title} <span className="text-gold">{content.accent}</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            {content.description}
          </p>
        </motion.div>

        {sectionImage ? (
          <img
            src={sectionImage}
            alt={content.illustration_alt || content.title || "Skills"}
            className="mb-10 h-56 w-full rounded-2xl border border-border object-cover shadow-premium"
          />
        ) : null}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
          {skillGroups.map((group, groupIndex) => {
            const Icon = getSkillIcon(group.icon);
            const skills = normalizeStringList(group.skills);
            const groupImage = resolveMediaUrl(group.image);
            return (
            <motion.div
              key={group.id}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: 0.1 + groupIndex * 0.1 }}
              className="card-premium p-6 md:p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                {groupImage ? (
                  <img src={groupImage} alt={group.image_alt || group.title} className="h-10 w-10 rounded-lg object-cover" />
                ) : (
                  <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                    <Icon className="h-5 w-5 text-gold" />
                  </div>
                )}
                <h3 className="text-xl font-semibold">{group.title}</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {skills.map((skill, skillIndex) => (
                  <motion.span
                    key={skill}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={isInView ? { opacity: 1, scale: 1 } : {}}
                    transition={{ duration: 0.3, delay: 0.2 + groupIndex * 0.1 + skillIndex * 0.03 }}
                    className="skill-chip"
                  >
                    {skill}
                  </motion.span>
                ))}
              </div>
            </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
