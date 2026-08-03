import { Code2, Server, Wrench, BookOpen } from "lucide-react";

export interface SkillGroup {
  id: string;
  title: string;
  icon: typeof Code2;
  skills: string[];
}

export const skillGroups: SkillGroup[] = [
  {
    id: "frontend",
    title: "Frontend",
    icon: Code2,
    skills: [
      "Vue 3",
      "Composition API",
      "TypeScript",
      "HTML5 / CSS3",
      "Tailwind CSS",
      "Адаптивная вёрстка",
      "SPA-архитектура",
      "State Management",
      "Формы и валидация"
    ]
  },
  {
    id: "backend",
    title: "Backend",
    icon: Server,
    skills: [
      "Python",
      "Django",
      "Django REST Framework",
      "Flask",
      "REST API",
      "PostgreSQL",
      "SQLAlchemy",
      "Auth / Roles",
      "Redis / Celery"
    ]
  },
  {
    id: "tools",
    title: "Инструменты",
    icon: Wrench,
    skills: [
      "Git / GitHub",
      "Docker / Compose",
      "Linux / VPS",
      "Nginx",
      "CI/CD (basic)",
      "VS Code",
      "Postman",
      "Figma (базово)"
    ]
  },
  {
    id: "practices",
    title: "Практики",
    icon: BookOpen,
    skills: [
      "Clean Code",
      "Рефакторинг",
      "Code Review",
      "Git Flow",
      "Документация",
      "Тестируемость",
      "API-контракты",
      "Agile / Kanban"
    ]
  }
];
