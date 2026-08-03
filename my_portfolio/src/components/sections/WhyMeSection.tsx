import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Check, Zap, Code2, Users, Shield, Target, Bug, Layout } from "lucide-react";

const reasons = [
  {
    icon: Code2,
    text: "Быстро разбираюсь в чужом коде и legacy-проектах"
  },
  {
    icon: Target,
    text: "Довожу задачи до рабочего результата"
  },
  {
    icon: Layout,
    text: "Понимаю полный цикл: frontend + backend + деплой"
  },
  {
    icon: Users,
    text: "Умею оценивать сроки/риски, коммуницировать с командой"
  },
  {
    icon: Shield,
    text: "Аккуратность к деталям UI и API-контрактам"
  },
  {
    icon: Zap,
    text: "Могу брать ответственность за модуль или фичу"
  },
  {
    icon: Bug,
    text: "Умею фиксить прод-проблемы и стабилизировать систему"
  }
];

export function WhyMeSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

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
            Почему <span className="text-gold">я подойду</span>
          </h2>
          <p className="text-muted-foreground text-lg text-center mb-12 max-w-2xl mx-auto">
            Качества, которые ценят работодатели и заказчики
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {reasons.map((reason, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                animate={isInView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.4, delay: 0.1 + index * 0.05 }}
                className="flex items-start gap-4 p-4 rounded-xl bg-card border border-border/50 hover:border-accent/30 transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                  <reason.icon className="h-5 w-5 text-gold" />
                </div>
                <p className="text-foreground leading-relaxed pt-2">{reason.text}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
