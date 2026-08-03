import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { HeroSection } from "@/components/sections/HeroSection";
import { AboutSection } from "@/components/sections/AboutSection";
import { SkillsSection } from "@/components/sections/SkillsSection";
import { ProjectsSection } from "@/components/sections/ProjectsSection";
import { WhyMeSection } from "@/components/sections/WhyMeSection";
import { MiddleChecklistSection } from "@/components/sections/MiddleChecklistSection";
import { ContactSection } from "@/components/sections/ContactSection";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <HeroSection />
        <AboutSection />
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
