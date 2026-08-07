import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  MessageCircle,
  Send,
  X,
} from "lucide-react";
import {
  createContext,
  FormEvent,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  groupPortfolioServicesByCategory,
  normalizePortfolioServices,
  submitPortfolioLead,
  usePortfolioSection,
} from "@/lib/tracknode";

interface ContactModalContextValue {
  openContactModal: (serviceTitle?: string) => void;
}

const ContactModalContext = createContext<ContactModalContextValue>({
  openContactModal: () => undefined,
});

export function useContactModal() {
  return useContext(ContactModalContext);
}

export function ContactModalProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [initialService, setInitialService] = useState("");

  const openContactModal = useCallback((serviceTitle = "") => {
    setInitialService(serviceTitle);
    setIsOpen(true);
  }, []);

  return (
    <ContactModalContext.Provider value={{ openContactModal }}>
      {children}
      <ContactModal
        isOpen={isOpen}
        initialService={initialService}
        onClose={() => setIsOpen(false)}
      />
    </ContactModalContext.Provider>
  );
}

function ContactModal({
  isOpen,
  initialService,
  onClose,
}: {
  isOpen: boolean;
  initialService: string;
  onClose: () => void;
}) {
  const servicesContent = usePortfolioSection<{ services?: unknown[] }>("services");
  const services = useMemo(
    () => normalizePortfolioServices(servicesContent.services),
    [servicesContent.services],
  );
  const groupedServices = useMemo(() => groupPortfolioServicesByCategory(services), [services]);

  const firstInputRef = useRef<HTMLInputElement | null>(null);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [serviceTitle, setServiceTitle] = useState("");
  const [comment, setComment] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitState, setSubmitState] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!isOpen) return;
    setServiceTitle(initialService || "");
    setSubmitState("idle");
    setErrors({});
    setMessage("");
    window.setTimeout(() => firstInputRef.current?.focus(), 80);
  }, [initialService, isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  const validate = () => {
    const nextErrors: Record<string, string> = {};
    const digits = phone.replace(/\D/g, "");
    if (!name.trim()) nextErrors.name = "Укажите имя.";
    if (!phone.trim() || digits.length < 10) nextErrors.phone = "Введите номер телефона полностью.";
    if (!serviceTitle.trim()) nextErrors.service = "Выберите услугу.";
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitState === "submitting" || !validate()) return;

    setSubmitState("submitting");
    setMessage("");
    try {
      await submitPortfolioLead({
        name: name.trim(),
        phone: phone.trim(),
        serviceTitle: serviceTitle.trim(),
        comment: comment.trim(),
      });
      setName("");
      setPhone("");
      setServiceTitle("");
      setComment("");
      setSubmitState("success");
      setMessage("Спасибо! Заявка отправлена. Я свяжусь с вами в ближайшее время.");
    } catch (error) {
      setSubmitState("error");
      setMessage(error instanceof Error ? error.message : "Не удалось отправить заявку. Попробуйте еще раз.");
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-[80] flex items-center justify-center bg-background/75 p-4 backdrop-blur-md"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={onClose}
        >
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="portfolio-contact-title"
            className="relative max-h-[calc(100vh-2rem)] w-full max-w-xl overflow-y-auto rounded-2xl border border-border bg-card shadow-premium-lg"
            initial={{ opacity: 0, y: 18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              onClick={onClose}
              className="absolute right-4 top-4 inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-background/80 text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Закрыть форму"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="p-6 sm:p-8">
              <div className="mb-6 pr-12">
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-full bg-accent/10 text-gold">
                  <MessageCircle className="h-5 w-5" />
                </div>
                <h2 id="portfolio-contact-title" className="text-2xl font-bold leading-tight">
                  Связаться
                </h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Оставьте контакты и выберите задачу. Ответ придет без перезагрузки страницы.
                </p>
              </div>

              {submitState === "success" ? (
                <div className="rounded-xl border border-accent/30 bg-accent/10 p-5">
                  <CheckCircle2 className="mb-3 h-7 w-7 text-gold" />
                  <p className="font-semibold">{message}</p>
                  <Button type="button" onClick={onClose} className="mt-5 rounded-full">
                    Закрыть
                  </Button>
                </div>
              ) : (
                <form className="space-y-5" onSubmit={handleSubmit} noValidate>
                  <div>
                    <label htmlFor="contact-name" className="mb-2 block text-sm font-medium">
                      Имя
                    </label>
                    <input
                      ref={firstInputRef}
                      id="contact-name"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      placeholder="Как к вам обращаться?"
                      className="h-12 w-full rounded-xl border border-input bg-background px-4 text-base outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-accent focus:ring-2 focus:ring-accent/20"
                      aria-invalid={Boolean(errors.name)}
                    />
                    {errors.name ? <p className="mt-2 text-sm text-destructive">{errors.name}</p> : null}
                  </div>

                  <div>
                    <label htmlFor="contact-phone" className="mb-2 block text-sm font-medium">
                      Номер телефона
                    </label>
                    <input
                      id="contact-phone"
                      value={phone}
                      onChange={(event) => setPhone(event.target.value)}
                      placeholder="+7 999 123-45-67"
                      inputMode="tel"
                      autoComplete="tel"
                      className="h-12 w-full rounded-xl border border-input bg-background px-4 text-base outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-accent focus:ring-2 focus:ring-accent/20"
                      aria-invalid={Boolean(errors.phone)}
                    />
                    {errors.phone ? <p className="mt-2 text-sm text-destructive">{errors.phone}</p> : null}
                  </div>

                  <div>
                    <label htmlFor="contact-service" className="mb-2 block text-sm font-medium">
                      Услуга
                    </label>
                    <select
                      id="contact-service"
                      value={serviceTitle}
                      onChange={(event) => setServiceTitle(event.target.value)}
                      className="h-12 w-full appearance-none rounded-xl border border-input bg-background px-4 text-base outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-accent/20"
                      aria-invalid={Boolean(errors.service)}
                    >
                      <option value="">Выберите услугу</option>
                      {groupedServices.map((group) => (
                        <optgroup key={group.key} label={group.label}>
                          {group.services.map((service) => (
                            <option key={service.id || service.title} value={service.title}>
                              {service.title}
                            </option>
                          ))}
                        </optgroup>
                      ))}
                    </select>
                    {errors.service ? <p className="mt-2 text-sm text-destructive">{errors.service}</p> : null}
                  </div>

                  <div>
                    <label htmlFor="contact-comment" className="mb-2 block text-sm font-medium">
                      Комментарий
                    </label>
                    <textarea
                      id="contact-comment"
                      value={comment}
                      onChange={(event) => setComment(event.target.value)}
                      placeholder="Кратко опишите, что нужно сделать"
                      rows={4}
                      className="min-h-28 w-full resize-y rounded-xl border border-input bg-background px-4 py-3 text-base outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-accent focus:ring-2 focus:ring-accent/20"
                    />
                  </div>

                  {submitState === "error" ? (
                    <div className="flex gap-3 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm">
                      <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-destructive" />
                      <p>{message}</p>
                    </div>
                  ) : null}

                  <Button
                    type="submit"
                    disabled={submitState === "submitting"}
                    className="h-12 w-full rounded-full bg-foreground text-background hover:bg-foreground/90"
                  >
                    {submitState === "submitting" ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Отправляем
                      </>
                    ) : (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        Оставить заявку
                      </>
                    )}
                  </Button>
                </form>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
