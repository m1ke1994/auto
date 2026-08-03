import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Code2, RefreshCw, Plug, Bot, Server } from "lucide-react";

const services = [
  {
    icon: Code2,
    title: "Разработка веб-приложений",
    description: "SPA, дашборды, CRM-системы под ваши бизнес-задачи"
  },
  {
    icon: RefreshCw,
    title: "Доработка и стабилизация",
    description: "Исправление багов, рефакторинг, оптимизация legacy-кода"
  },
  {
    icon: Plug,
    title: "API и интеграции",
    description: "REST API, webhooks, подключение внешних сервисов"
  },
  {
    icon: Bot,
    title: "Telegram-боты",
    description: "Боты для автоматизации процессов и работы с клиентами"
  },
  {
    icon: Server,
    title: "Деплой и инфраструктура",
    description: "VPS, Docker, Nginx — настройка и поддержка окружений"
  }
];

export function AboutSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

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
            Обо <span className="text-gold">мне</span>
          </h2>
          <div className="space-y-4 text-muted-foreground text-lg leading-relaxed">
            <p>
              Я fullstack-разработчик с опытом создания веб-приложений на стеке Vue.js + Django. 
              Работаю с проектами от MVP до production-ready решений.
            </p>
            <p>
              Моя сильная сторона — быстро разбираться в чужом коде, находить и исправлять проблемы, 
              доводить задачи до рабочего результата. Понимаю полный цикл разработки: от проектирования 
              БД и API до frontend-компонентов и деплоя.
            </p>
            <p>
              Открыт для проектной работы, доработки существующих систем и долгосрочного сотрудничества.
            </p>
          </div>
        </motion.div>

        {/* Services */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <h3 className="text-xl font-semibold mb-8">Чем я могу помочь</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((service, index) => (
              <motion.div
                key={service.title}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
                className="card-premium p-6 hover-lift group"
              >
                <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 group-hover:bg-accent/20 transition-colors">
                  <service.icon className="h-6 w-6 text-gold" />
                </div>
                <h4 className="font-semibold mb-2">{service.title}</h4>
                <p className="text-sm text-muted-foreground">{service.description}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
