"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
    Building,
    Search,
    MapPin,
    Users,
    Star,
    Calendar,
    Briefcase,
    Heart,
    HeartOff,
    CheckCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { ContactCompanyDialog } from "@/components/companies/contact-company-dialog";
import { ViewCompanyJobsDialog } from "@/components/companies/view-company-jobs-dialog";
import { WalletConnectionPrompt } from "@/components/dashboard/wallet-connection-prompt";

// Mock company data - will be replaced with real API calls
const mockCompanies = [
    {
        id: 1,
        name: "TechCorp Inc.",
        industry: "Technology",
        size: "500-1000 employees",
        location: "San Francisco, CA",
        founded: "2015",
        website: "https://techcorp.com",
        description: "Leading technology company specializing in AI and machine learning solutions for enterprise clients.",
        rating: 4.5,
        reviews: 128,
        openPositions: 12,
        skills: ["AI/ML", "Cloud Computing", "Data Science", "Software Engineering"],
        benefits: ["Health Insurance", "Remote Work", "Stock Options", "Flexible Hours"],
        featured: true,
        verified: true,
        hiringStatus: "actively-hiring" as const,
        departments: ["Engineering", "Product", "Design", "Sales", "Marketing", "Operations"],
        contactInfo: {
            email: "contact@techcorp.com",
            phone: "+1 (555) 123-4567",
            address: "123 Tech Street, San Francisco, CA 94105",
            linkedin: "https://linkedin.com/company/techcorp",
            twitter: "https://twitter.com/techcorp"
        }
    },
    {
        id: 2,
        name: "Hedera Labs",
        industry: "Blockchain",
        size: "100-250 employees",
        location: "Remote",
        founded: "2020",
        website: "https://hederalabs.com",
        description: "Innovative blockchain company building the future of decentralized applications on the Hedera network.",
        rating: 4.8,
        reviews: 89,
        openPositions: 8,
        skills: ["Blockchain", "Smart Contracts", "Hedera", "Web3"],
        benefits: ["Remote Work", "Crypto Payments", "Flexible Hours", "Learning Budget"],
        featured: true,
        verified: true,
        hiringStatus: "actively-hiring" as const,
        departments: ["Engineering", "Research", "Business Development", "Community"],
        contactInfo: {
            email: "hello@hederalabs.com",
            phone: "+1 (555) 987-6543",
            address: "456 Blockchain Ave, Virtual Office",
            linkedin: "https://linkedin.com/company/hedera-labs",
            twitter: "https://twitter.com/hederalabs"
        }
    },
    {
        id: 3,
        name: "Design Studio Pro",
        industry: "Design",
        size: "50-100 employees",
        location: "New York, NY",
        founded: "2018",
        website: "https://designstudiopro.com",
        description: "Creative design agency helping brands create meaningful digital experiences through innovative design solutions.",
        rating: 4.3,
        reviews: 67,
        openPositions: 5,
        skills: ["UI/UX Design", "Graphic Design", "Branding", "Prototyping"],
        benefits: ["Health Insurance", "Creative Freedom", "Professional Development", "Team Events"],
        featured: false,
        verified: true,
        hiringStatus: "selective-hiring" as const,
        departments: ["Design", "Creative", "Strategy", "Client Services"],
        contactInfo: {
            email: "info@designstudiopro.com",
            phone: "+1 (555) 456-7890",
            address: "789 Design Lane, New York, NY 10001",
            linkedin: "https://linkedin.com/company/design-studio-pro",
            twitter: "https://twitter.com/designstudiopro"
        }
    },
    {
        id: 4,
        name: "Cloud Solutions Ltd",
        industry: "Cloud Services",
        size: "250-500 employees",
        location: "Austin, TX",
        founded: "2016",
        website: "https://cloudsolutions.com",
        description: "Enterprise cloud infrastructure company providing scalable solutions for businesses of all sizes.",
        rating: 4.1,
        reviews: 156,
        openPositions: 15,
        skills: ["Cloud Computing", "DevOps", "Infrastructure", "Security"],
        benefits: ["Health Insurance", "Remote Work", "Competitive Salary", "401k"],
        featured: false,
        verified: true,
        hiringStatus: "actively-hiring" as const,
        departments: ["Engineering", "DevOps", "Sales", "Support", "Security"],
        contactInfo: {
            email: "contact@cloudsolutions.com",
            phone: "+1 (555) 321-0987",
            address: "321 Cloud Drive, Austin, TX 73301",
            linkedin: "https://linkedin.com/company/cloud-solutions-ltd",
            twitter: "https://twitter.com/cloudsolutions"
        }
    },
    {
        id: 5,
        name: "Green Energy Co",
        industry: "Renewable Energy",
        size: "1000+ employees",
        location: "Denver, CO",
        founded: "2012",
        website: "https://greenenergy.com",
        description: "Sustainable energy company focused on renewable energy solutions and environmental impact reduction.",
        rating: 4.6,
        reviews: 234,
        openPositions: 20,
        skills: ["Renewable Energy", "Engineering", "Sustainability", "Project Management"],
        benefits: ["Health Insurance", "Environmental Impact", "Professional Growth", "Competitive Benefits"],
        featured: true,
        verified: true,
        hiringStatus: "selective-hiring" as const,
        departments: ["Engineering", "Operations", "Research", "Sales", "Sustainability"],
        contactInfo: {
            email: "info@greenenergy.com",
            phone: "+1 (555) 654-3210",
            address: "654 Green Street, Denver, CO 80202",
            linkedin: "https://linkedin.com/company/green-energy-co",
            twitter: "https://twitter.com/greenenergyco"
        }
    }
];

const industries = ["All Industries", "Technology", "Blockchain", "Design", "Cloud Services", "Renewable Energy", "Finance", "Healthcare"];
const companySizes = ["All Sizes", "1-10", "11-50", "51-100", "101-250", "251-500", "501-1000", "1000+"];
const locations = ["All Locations", "San Francisco", "New York", "Remote", "Austin", "Denver", "Seattle", "Boston"];

export default function CompaniesPage() {
    const { isConnected } = useAuth();
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedIndustry, setSelectedIndustry] = useState("All Industries");
    const [selectedSize, setSelectedSize] = useState("All Sizes");
    const [selectedLocation, setSelectedLocation] = useState("All Locations");
    const [favoriteCompanies, setFavoriteCompanies] = useState<number[]>([]);
    const [contactSubmissions, setContactSubmissions] = useState<number[]>([]);
    const [showSuccessMessage, setShowSuccessMessage] = useState(false);

    // Filter companies based on search and filters
    const filteredCompanies = mockCompanies.filter(company => {
        const matchesSearch = company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            company.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
            company.skills.some(skill => skill.toLowerCase().includes(searchTerm.toLowerCase()));

        const matchesIndustry = selectedIndustry === "All Industries" || company.industry === selectedIndustry;
        const matchesSize = selectedSize === "All Sizes" || company.size === selectedSize;
        const matchesLocation = selectedLocation === "All Locations" ||
            company.location.toLowerCase().includes(selectedLocation.toLowerCase());

        return matchesSearch && matchesIndustry && matchesSize && matchesLocation;
    });

    const toggleFavorite = (companyId: number) => {
        setFavoriteCompanies(prev =>
            prev.includes(companyId)
                ? prev.filter(id => id !== companyId)
                : [...prev, companyId]
        );
    };

    if (!isConnected) {
        return (
            <WalletConnectionPrompt
                title="Connect to Browse Companies"
                description="Connect your Hedera wallet to explore company profiles and discover job opportunities."
            />
        );
    }

    return (
        <div className="w-full">
            <div className="">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="mb-8"
                >
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                        <div>
                            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                                Company Profiles
                            </h1>
                            <p className="text-slate-600 dark:text-slate-400 mt-2">
                                Discover companies and explore their culture, benefits, and opportunities
                            </p>
                        </div>
                        <div className="flex items-center gap-3">
                            <Badge variant="secondary" className="text-sm">
                                {filteredCompanies.length} companies
                            </Badge>
                            <Button variant="outline" size="sm">
                                <Heart className="w-4 h-4 mr-2" />
                                Favorites ({favoriteCompanies.length})
                            </Button>
                        </div>
                    </div>
                </motion.div>

                {/* Success Message */}
                {showSuccessMessage && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg"
                    >
                        <div className="flex items-center gap-2">
                            <CheckCircle className="w-5 h-4 text-green-500" />
                            <span className="text-green-700 dark:text-green-300 font-medium">
                                Contact message sent successfully! The company will get back to you soon.
                            </span>
                        </div>
                    </motion.div>
                )}

                {/* Filters and Search */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1 }}
                    className="mb-8"
                >
                    <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                        <CardContent className="p-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                {/* Search */}
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                                    <Input
                                        type="text"
                                        placeholder="Search companies, industries, skills..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        className="pl-10"
                                    />
                                </div>

                                {/* Industry Filter */}
                                <Select value={selectedIndustry} onValueChange={setSelectedIndustry}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {industries.map((industry) => (
                                            <SelectItem key={industry} value={industry}>
                                                {industry}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>

                                {/* Company Size Filter */}
                                <Select value={selectedSize} onValueChange={setSelectedSize}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {companySizes.map((size) => (
                                            <SelectItem key={size} value={size}>
                                                {size}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>

                                {/* Location Filter */}
                                <Select value={selectedLocation} onValueChange={setSelectedLocation}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {locations.map((location) => (
                                            <SelectItem key={location} value={location}>
                                                {location}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Companies Grid */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="grid grid-cols-1 lg:grid-cols-2 gap-6"
                >
                    {filteredCompanies.map((company, index) => (
                        <motion.div
                            key={company.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.1 * index }}
                        >
                            <Card className={`group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50 ${company.featured ? 'ring-2 ring-hedera-200 dark:ring-hedera-800' : ''
                                }`}>
                                <CardContent className="p-6">
                                    {/* Company Header */}
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-start gap-4">
                                            <div className="w-16 h-16 bg-gradient-to-br from-hedera-500 to-hedera-600 rounded-xl flex items-center justify-center flex-shrink-0">
                                                <Building className="w-8 h-8 text-white" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h3 className="text-xl font-semibold text-slate-900 dark:text-white group-hover:text-hedera-600 transition-colors">
                                                        {company.name}
                                                    </h3>
                                                    {company.verified && (
                                                        <Badge variant="secondary" className="text-xs">
                                                            Verified
                                                        </Badge>
                                                    )}
                                                    {company.featured && (
                                                        <Badge className="text-xs bg-gradient-to-r from-hedera-500 to-hedera-600">
                                                            Featured
                                                        </Badge>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
                                                    <div className="flex items-center gap-1">
                                                        <Briefcase className="w-4 h-4" />
                                                        {company.industry}
                                                    </div>
                                                    <div className="flex items-center gap-1">
                                                        <Users className="w-4 h-4" />
                                                        {company.size}
                                                    </div>
                                                    <div className="flex items-center gap-1">
                                                        <MapPin className="w-4 h-4" />
                                                        {company.location}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Favorite Button */}
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => toggleFavorite(company.id)}
                                            className={`h-8 w-8 p-0 ${favoriteCompanies.includes(company.id)
                                                ? 'text-red-500 hover:text-red-600'
                                                : 'text-slate-400 hover:text-slate-600'
                                                }`}
                                        >
                                            {favoriteCompanies.includes(company.id) ? (
                                                <Heart className="w-4 h-4 fill-current" />
                                            ) : (
                                                <HeartOff className="w-4 h-4" />
                                            )}
                                        </Button>
                                    </div>

                                    {/* Company Description */}
                                    <p className="text-slate-600 dark:text-slate-400 mb-4 leading-relaxed">
                                        {company.description}
                                    </p>

                                    {/* Company Stats */}
                                    <div className="grid grid-cols-3 gap-4 mb-4">
                                        <div className="text-center">
                                            <div className="flex items-center justify-center gap-1 mb-1">
                                                <Star className="w-4 h-4 text-yellow-500 fill-current" />
                                                <span className="font-semibold text-slate-900 dark:text-white">
                                                    {company.rating}
                                                </span>
                                            </div>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                {company.reviews} reviews
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <div className="font-semibold text-slate-900 dark:text-white mb-1">
                                                {company.openPositions}
                                            </div>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                Open positions
                                            </p>
                                        </div>
                                        <div className="text-center">
                                            <div className="font-semibold text-slate-900 dark:text-white mb-1">
                                                {company.founded}
                                            </div>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                Founded
                                            </p>
                                        </div>
                                    </div>

                                    {/* Skills */}
                                    <div className="mb-4">
                                        <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-2">
                                            Key Skills
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {company.skills.map((skill) => (
                                                <Badge key={skill} variant="secondary" className="text-xs">
                                                    {skill}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Benefits */}
                                    <div className="mb-4">
                                        <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-2">
                                            Benefits
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {company.benefits.map((benefit) => (
                                                <Badge key={benefit} variant="outline" className="text-xs">
                                                    {benefit}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-700">
                                        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                                            <Calendar className="w-4 h-4" />
                                            Founded {company.founded}
                                        </div>
                                        <div className="flex gap-2">
                                            {contactSubmissions.includes(company.id) ? (
                                                <Button variant="outline" size="sm" className="text-green-600 border-green-600" disabled>
                                                    <CheckCircle className="w-4 h-4 mr-2" />
                                                    Contacted
                                                </Button>
                                            ) : (
                                                <>
                                                    <ContactCompanyDialog
                                                        company={company}
                                                        onContactSubmitted={(contact) => {
                                                            console.log('Contact submitted:', contact);
                                                            setContactSubmissions(prev => [...prev, company.id]);
                                                            setShowSuccessMessage(true);
                                                            setTimeout(() => setShowSuccessMessage(false), 5000);
                                                        }}
                                                    />
                                                    <ViewCompanyJobsDialog
                                                        company={{
                                                            ...company,
                                                            jobs: [] // The modal will generate its own mock jobs
                                                        }}
                                                        onJobApplied={(jobId) => {
                                                            console.log('Job applied:', jobId);
                                                            // TODO: Handle job application
                                                        }}
                                                    />
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ))}

                    {/* Empty State */}
                    {filteredCompanies.length === 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6 }}
                            className="col-span-full text-center py-12"
                        >
                            <Building className="w-16 h-16 mx-auto text-slate-400 mb-4" />
                            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                                No companies found
                            </h3>
                            <p className="text-slate-600 dark:text-slate-400 mb-6">
                                Try adjusting your search criteria or check back later for new companies.
                            </p>
                            <Button
                                onClick={() => {
                                    setSearchTerm("");
                                    setSelectedIndustry("All Industries");
                                    setSelectedSize("All Sizes");
                                    setSelectedLocation("All Locations");
                                }}
                                variant="outline"
                            >
                                Clear Filters
                            </Button>
                        </motion.div>
                    )}
                </motion.div>
            </div>
        </div>
    );
}
