import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { HeroSection } from "@/components/sections/HeroSection";
import { AboutSection } from "@/components/sections/AboutSection";
import { ServicesSection } from "@/components/sections/ServicesSection";
import { SkillsSection } from "@/components/sections/SkillsSection";
import { ProjectsSection } from "@/components/sections/ProjectsSection";
import { WhyMeSection } from "@/components/sections/WhyMeSection";
import { MiddleChecklistSection } from "@/components/sections/MiddleChecklistSection";
import { ContactSection } from "@/components/sections/ContactSection";
import { usePortfolioStatus } from "@/lib/tracknode";

const Index = () => {
  const { isLoading, error } = usePortfolioStatus();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4 text-center">
        <div>
          <div className="mx-auto mb-5 h-12 w-12 rounded-full border-2 border-border border-t-gold animate-spin" />
          <p className="text-sm text-muted-foreground">Загружаем сайт</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      {error ? (
        <div className="fixed bottom-4 left-1/2 z-[70] w-[calc(100%-2rem)] max-w-md -translate-x-1/2 rounded-xl border border-border bg-card px-4 py-3 text-sm text-muted-foreground shadow-premium">
          {error}
        </div>
      ) : null}
      <main>
        <HeroSection />
        <AboutSection />
        <ServicesSection />
        <SkillsSection />
        <ProjectsSection />
        <WhyMeSection />
        <MiddleChecklistSection />
        <ContactSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
