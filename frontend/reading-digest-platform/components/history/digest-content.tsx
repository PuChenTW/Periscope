import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ExternalLink, Clock, Calendar, Rss, Share, Download } from "lucide-react"

interface DigestContentProps {
  digestId: string
}

const MOCK_DIGEST = {
  id: "1",
  date: "December 19, 2024",
  deliveryTime: "8:00 AM EST",
  articleCount: 47,
  readTime: "12 min",
  summary:
    "Today's digest covers breakthrough developments in AI, climate policy updates, and emerging startup trends.",
  sections: [
    {
      title: "Technology & AI",
      articles: [
        {
          title: "OpenAI Announces GPT-5 with Revolutionary Capabilities",
          source: "TechCrunch",
          publishedAt: "2 hours ago",
          summary:
            "OpenAI has unveiled GPT-5, featuring unprecedented reasoning abilities and multimodal understanding. The new model demonstrates significant improvements in mathematical problem-solving and creative tasks.",
          url: "https://techcrunch.com/gpt-5-announcement",
          readTime: "3 min",
        },
        {
          title: "Quantum Computing Breakthrough Achieved by IBM Research",
          source: "MIT Technology Review",
          publishedAt: "4 hours ago",
          summary:
            "IBM researchers have successfully demonstrated quantum error correction at scale, bringing practical quantum computing applications significantly closer to reality.",
          url: "https://technologyreview.com/quantum-breakthrough",
          readTime: "4 min",
        },
      ],
    },
    {
      title: "Climate & Environment",
      articles: [
        {
          title: "Global Climate Summit Reaches Historic Agreement",
          source: "BBC News",
          publishedAt: "6 hours ago",
          summary:
            "World leaders at COP29 have agreed to unprecedented climate action measures, including a $500 billion fund for renewable energy transition in developing countries.",
          url: "https://bbc.com/climate-summit-agreement",
          readTime: "5 min",
        },
        {
          title: "Revolutionary Solar Panel Technology Achieves 50% Efficiency",
          source: "Nature",
          publishedAt: "8 hours ago",
          summary:
            "Scientists have developed a new type of solar panel using perovskite-silicon tandem cells that achieves record-breaking 50% efficiency in laboratory conditions.",
          url: "https://nature.com/solar-efficiency-breakthrough",
          readTime: "3 min",
        },
      ],
    },
    {
      title: "Business & Startups",
      articles: [
        {
          title: "AI Startup Anthropic Raises $4B in Series C Funding",
          source: "VentureBeat",
          publishedAt: "1 day ago",
          summary:
            "Anthropic, the AI safety company, has secured $4 billion in Series C funding led by Google and Amazon, valuing the company at $18 billion.",
          url: "https://venturebeat.com/anthropic-funding",
          readTime: "2 min",
        },
      ],
    },
  ],
}

export function DigestContent({ digestId }: DigestContentProps) {
  const digest = MOCK_DIGEST // In real app, fetch by digestId

  return (
    <div className="space-y-6">
      {/* Digest Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-2xl mb-2">Daily Digest</CardTitle>
              <CardDescription className="text-base">{digest.summary}</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Share className="w-4 h-4 mr-2" />
                Share
              </Button>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              {digest.date}
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Delivered at {digest.deliveryTime}
            </div>
            <div className="flex items-center gap-2">
              <Rss className="w-4 h-4" />
              {digest.articleCount} articles
            </div>
            <Badge variant="secondary">{digest.readTime} read time</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Digest Sections */}
      {digest.sections.map((section, sectionIndex) => (
        <Card key={sectionIndex}>
          <CardHeader>
            <CardTitle className="text-xl">{section.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {section.articles.map((article, articleIndex) => (
                <div key={articleIndex}>
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <h3 className="text-lg font-semibold leading-tight">{article.title}</h3>
                      <Button variant="ghost" size="sm" asChild>
                        <a href={article.url} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </Button>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="font-medium">{article.source}</span>
                      <span>{article.publishedAt}</span>
                      <Badge variant="outline" className="text-xs">
                        {article.readTime}
                      </Badge>
                    </div>

                    <p className="text-muted-foreground leading-relaxed">{article.summary}</p>

                    <Button variant="outline" size="sm" asChild>
                      <a href={article.url} target="_blank" rel="noopener noreferrer">
                        Read Full Article
                        <ExternalLink className="w-4 h-4 ml-2" />
                      </a>
                    </Button>
                  </div>

                  {articleIndex < section.articles.length - 1 && <Separator className="mt-6" />}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
