import asyncio
import nest_asyncio
import time

from typing import Any
from autogen import config_list_from_json, UserProxyAgent
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group.patterns import AutoPattern
from agents.intake_agent import IntakeAgent
from agents.company_research_agent import CompanyResearchAgent
from agents.people_finder_agent import PeopleFinderAgent
from agents.contact_enrichment_agent import ContactEnrichmentAgent
from agents.lead_scoring_agent import LeadScoringAgent
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

nest_asyncio.apply()
app = FastAPI()

# confige CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "127.0.0.1.*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

companyTestData = """
{
  "company_list": [
    {
      "name": "Westport Fuel Systems",
      "website": "https://www.westport.com",
      "description": "Westport Fuel Systems is a global leader in the design, manufacture, and supply of advanced fuel systems for clean, low-carbon fuels.",
      "industry": "Automotive Parts and Manufacturing",
      "location": "Vancouver, BC, Canada",
      "employee_count": "100-150",
      "annual_revenue": "$30M-$40M",
      "relevant_info": "Westport is a good fit for StreamERP due to its focus on clean energy solutions, which likely involves digital transformation, and operates multiple sites.",
      "relevance_score": 85
    },
    {
      "name": "Magna Seating",
      "website": "https://www.magnainc.com",
      "description": "Magna Seating is part of Magna International, specializing in seating solutions for the automotive industry.",
      "industry": "Automotive Parts",
      "location": "Aurora, ON, Canada",
      "employee_count": "100-200",
      "annual_revenue": "$20M-$50M",
      "relevant_info": "As part of Magna, this division likely undergoes digital transformation and operates multiple production sites.",
      "relevance_score": 90
    },
    {
      "name": "Martinrea International Inc.",
      "website": "https://www.martinrea.com",
      "description": "Martinrea International Inc. is a diversified global automotive supplier that provides lightweight castings, aluminum blocks, structural components, and fluid management systems.",
      "industry": "Automotive Parts",
      "location": "Vaughan, ON, Canada",
      "employee_count": "100-200",
      "annual_revenue": "$20M-$50M",
      "relevant_info": "Martinrea is a good fit due to its diverse operations and likely need for digital transformation across multiple sites.",
      "relevance_score": 92
    },
    {
      "name": "Accuride Corporation",
      "website": "https://www.accuridewheels.com",
      "description": "Accuride Corporation is a leading supplier of wheel end solutions to the global commercial vehicle industry.",
      "industry": "Automotive Parts",
      "location": "Evansville, IN, USA",
      "employee_count": "100-200",
      "annual_revenue": "$20M-$50M",
      "relevant_info": "Accuride operates multiple production sites and is likely undergoing digital transformation in its operations.",
      "relevance_score": 88
    },
    {
      "name": "Linamar Corporation",
      "website": "https://www.linamar.com",
      "description": "Linamar Corporation is a diversified global manufacturing company of highly engineered products across its Powertrain and Driveline, Industrial, and Skyjack segments.",
      "industry": "Automotive Parts and Manufacturing",
      "location": "Guelph, ON, Canada",
      "employee_count": "100-200",
      "annual_revenue": "$20M-$50M",
      "relevant_info": "Linamar operates multiple production sites and is likely undergoing digital transformation in its operations.",
      "relevance_score": 90
    }
  ]
}
"""

companyListWithPeopleTestData = """
{
    "company_list": [
        {
            "company_info": {
                "name": "Westport Fuel Systems",
                "website": "https://www.westport.com",
                "description": "Westport Fuel Systems is a global leader in the design, manufacture, and supply of advanced fuel systems for clean, low-carbon fuels.",
                "industry": "Automotive Parts and Manufacturing",
                "location": "Vancouver, BC, Canada",
                "employee_count": "100-150",
                "annual_revenue": "$30M-$40M",
                "relevant_info": "Westport is a good fit for StreamERP due to its focus on clean energy solutions, which likely involves digital transformation, and operates multiple sites.",
                "relevance_score": 85,
                "people_list": [
                    {
                        "person_info": {
                            "name": "Dan Sceli",
                            "title": "CEO & Director",
                            "email": "dsceli@wfsinc.com",
                            "phone": "(604) 718-2000",
                            "linkedin": "",
                            "relevant_info": "Dan Sceli is the CEO and Director of Westport Fuel Systems, responsible for strategic direction. His leadership in manufacturing and commitment to sustainability aligns with the ERP solution's focus on operational efficiency and environmental sustainability.",
                            "relevance_score": 85,
                            "approach_recommendation": "Approach Dan Sceli by highlighting how StreamERP can enhance operational efficiency and support sustainability goals in the automotive manufacturing sector.",
                            "notes": "The email is a best-guess assumption based on the pattern d***@wfsinc.com from ZoomInfo and the publicly available (604) 718-2000 corporate phone number for Westport Fuel Systems.",
                            "source_urls": [
                                "https://wfsinc.com/company/leadership",
                                "https://investors.wfsinc.com/news/news-details/2024/Westport-Appoints-Dan-Sceli-as-Chief-Executive-Officer/default.aspx"
                            ]
                        }
                    }
                ]
            }
        },
        {
            "company_info": {
                "name": "Magna Seating",
                "website": "https://www.magnainc.com",
                "description": "Magna Seating is part of Magna International, specializing in seating solutions for the automotive industry.",
                "industry": "Automotive Parts",
                "location": "Aurora, ON, Canada",
                "employee_count": "100-200",
                "annual_revenue": "$20M-$50M",
                "relevant_info": "As part of Magna, this division likely undergoes digital transformation and operates multiple production sites.",
                "relevance_score": 90,
                "people_list": [
                    {
                        "person_info": {
                            "name": "Simon Kew",
                            "title": "Vice President NA JIT Operations",
                            "email": "simon.kew@magna.com",
                            "phone": "248-420-....",
                            "linkedin": "",
                            "relevant_info": "Simon Kew is associated with Magna Seating and has been involved in various leadership roles.",
                            "relevance_score": 90,
                            "approach_recommendation": "Approach Simon Kew by highlighting the importance of automotive seating solutions and the potential for collaboration or innovation in the industry.",
                            "notes": "The role of Simon Kew is noted differently across sources; some mention him as President, while others specify Vice President NA JIT Operations.",
                            "source_urls": [
                                "https://www.lead411.com/Simon_Kew_30402291.html",
                                "https://contactout.com/simon-kew-76532",
                                "https://rocketreach.co/simon-kew-email_25130687"
                            ]
                        }
                    }
                ]
            }
        },
        {
            "company_info": {
                "name": "Martinrea International Inc.",
                "website": "https://www.martinrea.com",
                "description": "Martinrea International Inc. is a diversified global automotive supplier that provides lightweight castings, aluminum blocks, structural components, and fluid management systems.",
                "industry": "Automotive Parts",
                "location": "Vaughan, ON, Canada",
                "employee_count": "100-200",
                "annual_revenue": "$20M-$50M",
                "relevant_info": "Martinrea is a good fit due to its diverse operations and likely need for digital transformation across multiple sites.",
                "relevance_score": 92,
                "people_list": [
                    {
                        "person_info": {
                            "name": "Pat D'Eramo",
                            "title": "President and CEO",
                            "email": "",
                            "phone": "",
                            "linkedin": "",
                            "relevant_info": "Pat D'Eramo is the President and Chief Executive Officer of Martinrea International Inc., with extensive experience in metal forming and parts manufacturing.",
                            "relevance_score": 90,
                            "approach_recommendation": "Approach Pat D'Eramo by highlighting any collaboration or innovation opportunities in the automotive sector that align with Martinrea's focus on lightweight structures and propulsion systems.",
                            "notes": "Contact information for Pat D'Eramo is not readily available. The information provided is based on publicly available sources about his professional background and roles.",
                            "source_urls": [
                                "https://rocketreach.co/pat-deramo-email_87174236",
                                "https://www.martinrea.com/about-us/executive-team/",
                                "https://www.cadia.org/pat-deramo/"
                            ]
                        }
                    },
                    {
                        "person_info": {
                            "name": "Fred Di Tosto",
                            "title": "President",
                            "email": "f.ditosto@martinrea.com",
                            "phone": "(289) 982-3020",
                            "linkedin": "",
                            "relevant_info": "Fred Di Tosto serves as President for Martinrea International, based in Concord, Ontario effective July 1, 2024. He previously served as CFO since 2011 and has held other executive roles including EVP of its Flexible Manufacturing Group and EVP, Corporate Strategy.",
                            "relevance_score": 95,
                            "approach_recommendation": "I would approach Fred Di Tosto by saying: 'Hello Fred, I represent [your organization or product] and am reaching out regarding opportunities in automotive supply chain innovation and leadership. As President of Martinrea International, I believe you share our vision for operational excellence and growth. Would you be open to a brief conversation?'",
                            "notes": "The email is partially obscured in ZoomInfo; it is likely f.ditosto@martinrea.com, as this matches the company's standard email format and Fred's initials.",
                            "source_urls": [
                                "https://www.martinrea.com/press-release/fred-di-tosto-appointed-president-of-martinrea-international-inc/",
                                "https://www.zoominfo.com/p/Fred-Di-tosto/1610557662",
                                "https://financialpost.com/globe-newswire/fred-di-tosto-appointed-president-of-martinrea-international-inc"
                            ]
                        }
                    },
                    {
                        "person_info": {
                            "name": "Peter Cirulis",
                            "title": "CFO",
                            "email": "",
                            "phone": "",
                            "linkedin": "",
                            "relevant_info": "As CFO, Peter Cirulis is responsible for financial strategies and would be interested in the financial optimization aspects of StreamERP.",
                            "relevance_score": 95,
                            "approach_recommendation": "Emphasize how StreamERP can improve financial management and support growth initiatives.",
                            "notes": "Peter Cirulis's recent appointment as CFO indicates his critical role in financial decision-making.",
                            "source_urls": [
                                "https://www.martinrea.com/press-release/peter-cirulis-appointed-chief-financial-officer-of-martinrea-international-inc/",
                                "https://www.globaldata.com/company-profile/martinrea-international-inc/executives/"
                            ]
                        }
                    },
                    {
                        "person_info": {
                            "name": "Ganesh Iyer",
                            "title": "Chief Technology Officer",
                            "email": "ganesh.iyer@martinrea.com",
                            "phone": "",
                            "linkedin": "",
                            "relevant_info": "Ganesh Iyer leads all aspects of global engineering, product development, and IT at Martinrea International.",
                            "relevance_score": 75,
                            "approach_recommendation": "Approach Ganesh Iyer by highlighting technological advancements or innovative solutions in the automotive industry.",
                            "notes": "Email is an assumption based on common corporate email formats. The specific LinkedIn profile URL is not available in the search results.",
                            "source_urls": [
                                "https://www.martinrea.com/about-us/executive-team/",
                                "https://a-sp.org/governance/ganesh-iyer-a-sp-board-of-directors/"
                            ]
                        }
                    }
                ]
            }
        },
        {
            "company_info": {
                "name": "Accuride Corporation",
                "website": "https://www.accuridewheels.com",
                "description": "Accuride Corporation is a leading supplier of wheel end solutions to the global commercial vehicle industry.",
                "industry": "Automotive Parts",
                "location": "Evansville, IN, USA",
                "employee_count": "100-200",
                "annual_revenue": "$20M-$50M",
                "relevant_info": "Accuride operates multiple production sites and is likely undergoing digital transformation in its operations.",
                "relevance_score": 88,
                "people_list": [
                    {
                        "person_info": {
                            "name": "Skotti Fietsam",
                            "title": "Senior Vice President, Supply Chain and CIO",
                            "email": "s***@accuridecorp.com",
                            "phone": "(812) ***-****",
                            "linkedin": "",
                            "relevant_info": "Skotti Fietsam handles supply chain and IT responsibilities, making them a relevant contact for StreamERP.",
                            "relevance_score": 90,
                            "approach_recommendation": "Reach out to Skotti Fietsam by highlighting how StreamERP can improve supply chain efficiency and IT integration.",
                            "notes": "Skotti's role involves both supply chain and IT, making them a key decision maker for ERP solutions.",
                            "source_urls": [
                                "https://www.accuridecorp.com/about-accuride/leadership"
                            ]
                        }
                    },
                    {
                        "person_info": {
                            "name": "Geoff Bruce",
                            "title": "President of Accuride Wheels",
                            "email": "g******@accuridecorp.com",
                            "phone": "815288....",
                            "linkedin": "",
                            "relevant_info": "Geoff Bruce, as President of Accuride Wheels, could be interested in operational improvements offered by StreamERP.",
                            "relevance_score": 95,
                            "approach_recommendation": "Emphasize how StreamERP can enhance operational efficiency and customer delivery in the wheel manufacturing sector.",
                            "notes": "Geoff Bruce's role focuses on wheel operations, making him a potential decision maker for operational improvements.",
                            "source_urls": [
                                "https://thebrakereport.com/kent-jones-named-accuride-ceo/"
                            ]
                        }
                    },
                    {
                        "person_info": {
                            "name": "Kent Jones",
                            "title": "Chief Executive Officer",
                            "email": "",
                            "phone": "",
                            "linkedin": "",
                            "relevant_info": "Kent Jones, as CEO, oversees strategic growth and innovation, which could include adopting StreamERP for operational enhancements.",
                            "relevance_score": 95,
                            "approach_recommendation": "Approach Kent Jones by highlighting the strategic benefits of StreamERP in driving growth and innovation.",
                            "notes": "Kent Jones's role as CEO makes him a key decision maker for strategic initiatives like adopting new ERP solutions.",
                            "source_urls": [
                                "https://www.accuridecorp.com/accuride-names-kent-jones-as-chief-executive-officer"
                            ]
                        }
                    }
                ]
            }
        },
        {
            "company_info": {
                "name": "Linamar Corporation",
                "website": "https://www.linamar.com",
                "description": "Linamar Corporation is a diversified global manufacturing company of highly engineered products across its Powertrain and Driveline, Industrial, and Skyjack segments.",
                "industry": "Automotive Parts and Manufacturing",
                "location": "Guelph, ON, Canada",
                "employee_count": "100-200",
                "annual_revenue": "$20M-$50M",
                "relevant_info": "Linamar operates multiple production sites and is likely undergoing digital transformation in its operations.",
                "relevance_score": 90,
                "people_list": [
                    {
                        "person_info": {
                            "name": "Jim Jarrell",
                            "title": "CEO and President",
                            "email": "jim.jarrell@linamar.com",
                            "phone": "519-836-****",
                            "linkedin": "",
                            "relevant_info": "Jim Jarrell serves as the CEO and President of Linamar Corporation, responsible for overall strategic direction. His role involves overseeing major operations and strategic decisions which align with the need for ERP solutions.",
                            "relevance_score": 90,
                            "approach_recommendation": "Approach Jim Jarrell by highlighting strategic partnerships or innovative solutions that align with Linamar's global expansion and operational goals.",
                            "notes": "The phone number is partial and sourced from various directories. The LinkedIn profile was not found due to privacy settings or lack of public information.",
                            "source_urls": [
                                "https://www.linamar.com/team/jim-jarrell/",
                                "https://contactout.com/Jim-Jarrell-85575078",
                                "https://www.zoominfo.com/p/Jim-Jarrell/40390109"
                            ]
                        }
                    },
                    {
                        "person_info": {
                            "name": "Dale Schneider",
                            "title": "Chief Financial Officer",
                            "email": "d***@linamar.com",
                            "phone": "(519) ***-****",
                            "linkedin": "",
                            "relevant_info": "Dale Schneider is the CFO of Linamar Corporation, playing a crucial role in financial planning and investment decisions. His focus on financial management aligns with the cost optimization features of StreamERP.",
                            "relevance_score": 90,
                            "approach_recommendation": "I would approach Dale Schneider by emphasizing how StreamERP can help streamline financial operations and improve cost management across Linamar's operations.",
                            "notes": "The phone number and email are partially masked for privacy.",
                            "source_urls": [
                                "https://www.linamar.com/report/linamar-corporation-announces-the-appointment-of-dale-schneider-as-chief-financial-officer/",
                                "https://www.zoominfo.com/p/Dale-Schneider/1717114986"
                            ]
                        }
                    },
                    {
                        "person_info": {
                            "name": "Chris Merchant",
                            "title": "Global Vice President Of Finance & Information Technology",
                            "email": "",
                            "phone": "519-836-XXXX",
                            "linkedin": "",
                            "relevant_info": "Chris Merchant has been with Linamar Corporation since 1999 and has served as Global Vice President of Finance & Information Technology.",
                            "relevance_score": 85,
                            "approach_recommendation": "Contact through corporate channels or phone number provided. Consider reaching out via Linamar's corporate contact form referencing his title for appropriate routing.",
                            "notes": "Email addresses were not publicly provided in full; phone number partially obtained but not complete.",
                            "source_urls": [
                                "https://rocketreach.co/chris-merchant-email_25232531",
                                "https://theorg.com/org/linamar-corp/org-chart/chris-merchant",
                                "https://www.cpaontario.ca/protecting-the-public/directories/member/merchant-1l5c2b"
                            ]
                        }
                    },
                    {
                        "person_info": {
                            "name": "Roxanne Rose",
                            "title": "Vice President, Global Human Resources",
                            "email": "Roxanne.Rose@linamar.com",
                            "phone": "519-836-7550",
                            "linkedin": "",
                            "relevant_info": "Roxanne Rose is a seasoned professional with extensive experience in Human Resources. She is currently serving as the Vice President, Global Human Resources at Linamar Corporation.",
                            "relevance_score": 90,
                            "approach_recommendation": "I would approach Roxanne Rose by highlighting any expertise or solutions relevant to her role in Human Resources, such as innovative HR technologies or strategies for organizational development.",
                            "notes": "The phone number and email might be used for general inquiries or accessibility feedback rather than direct personal contact.",
                            "source_urls": [
                                "https://www.linamar.com/team/roxanne-rose/",
                                "https://rocketreach.co/roxanne-rose-email_7886431",
                                "https://www.linamar.com/wp-content/uploads/2024/01/Updated-Linamar-Feedback-Form.pdf"
                            ]
                        }
                    },
                    {
                        "person_info": {
                            "name": "Mark Stoddart",
                            "title": "Chief Technology Officer & Executive Vice President of Sales and Marketing",
                            "email": "m***@linamar.com",
                            "phone": "",
                            "linkedin": "",
                            "relevant_info": "Mark Stoddart is a seasoned executive with extensive experience in the automotive sector, joining Linamar in 1985.",
                            "relevance_score": 85,
                            "approach_recommendation": "I would approach Mark Stoddart by highlighting expertise in automotive technology and marketing strategies, emphasizing how your solutions align with Linamar's focus on innovative manufacturing solutions.",
                            "notes": "I couldn't find a complete, verified email address or a LinkedIn profile.",
                            "source_urls": [
                                "https://www.linamar.com/team/mark-stoddart/",
                                "https://www.enertechcapital.com/post/enertech-capital-adds-linamar-executive-mark-stoddart-to-mobility-advisory-board",
                                "https://www.zoominfo.com/p/Mark-Stoddart/265096096"
                            ]
                        }
                    }
                ]
            }
        }
    ]
}
"""

leadsTestData = """
{
    "complete": true,
    "leads_list": [
        {
            "name": "Dan Sceli",
            "title": "CEO & Director",
            "email": "dsceli@wfsinc.com",
            "phone": "(604) 718-2000",
            "linkedin": "",
            "relevant_info": "Dan Sceli is the CEO and Director of Westport Fuel Systems, responsible for strategic direction. His leadership in manufacturing and commitment to sustainability aligns with the ERP solution's focus on operational efficiency and environmental sustainability.",
            "relevance_score": 83,
            "approach_reccomendation": "Approach Dan Sceli by highlighting how StreamERP can enhance operational efficiency and support sustainability goals in the automotive manufacturing sector.",
            "notes": "The email is a best-guess assumption based on the pattern d***@wfsinc.com from ZoomInfo and the publicly available (604) 718-2000 corporate phone number for Westport Fuel Systems.",
            "source_urls": [
                "https://wfsinc.com/company/leadership",
                "https://investors.wfsinc.com/news/news-details/2024/Westport-Appoints-Dan-Sceli-as-Chief-Executive-Officer/default.aspx"
            ],
            "company_info": {
                "name": "Westport Fuel Systems",
                "website": "https://www.westport.com",
                "description": "Westport Fuel Systems is a global leader in the design, manufacture, and supply of advanced fuel systems for clean, low-carbon fuels.",
                "industry": "Automotive Parts and Manufacturing",
                "relevant_info": "Westport is a good fit for StreamERP due to its focus on clean energy solutions, which likely involves digital transformation, and operates multiple sites."
            }
        },
        {
            "name": "Simon Kew",
            "title": "Vice President NA JIT Operations",
            "email": "simon.kew@magna.com",
            "phone": "248-420-....",
            "linkedin": "",
            "relevant_info": "Simon Kew is associated with Magna Seating and has been involved in various leadership roles.",
            "relevance_score": 91,
            "approach_reccomendation": "Approach Simon Kew by highlighting the importance of automotive seating solutions and the potential for collaboration or innovation in the industry.",
            "notes": "The role of Simon Kew is noted differently across sources; some mention him as President, while others specify Vice President NA JIT Operations.",
            "source_urls": [
                "https://www.lead411.com/Simon_Kew_30402291.html",
                "https://contactout.com/simon-kew-76532",
                "https://rocketreach.co/simon-kew-email_25130687"
            ],
            "company_info": {
                "name": "Magna Seating",
                "website": "https://www.magnainc.com",
                "description": "Magna Seating is part of Magna International, specializing in seating solutions for the automotive industry.",
                "industry": "Automotive Parts",
                "relevant_info": "As part of Magna, this division likely undergoes digital transformation and operates multiple production sites."
            }
        },
        {
            "name": "Fred Di Tosto",
            "title": "President",
            "email": "f.ditosto@martinrea.com",
            "phone": "(289) 982-3020",
            "linkedin": "",
            "relevant_info": "Fred Di Tosto serves as President for Martinrea International, based in Concord, Ontario effective July 1, 2024. He previously served as CFO since 2011 and has held other executive roles including EVP of its Flexible Manufacturing Group and EVP, Corporate Strategy.",
            "relevance_score": 96,
            "approach_reccomendation": "I would approach Fred Di Tosto by saying: 'Hello Fred, I represent [your organization or product] and am reaching out regarding opportunities in automotive supply chain innovation and leadership. As President of Martinrea International, I believe you share our vision for operational excellence and growth. Would you be open to a brief conversation?'",
            "notes": "The email is partially obscured in ZoomInfo; it is likely f.ditosto@martinrea.com, as this matches the company's standard email format and Fred's initials.",
            "source_urls": [
                "https://www.martinrea.com/press-release/fred-di-tosto-appointed-president-of-martinrea-international-inc/",
                "https://www.zoominfo.com/p/Fred-Di-tosto/1610557662",
                "https://financialpost.com/globe-newswire/fred-di-tosto-appointed-president-of-martinrea-international-inc"
            ],
            "company_info": {
                "name": "Martinrea International Inc.",
                "website": "https://www.martinrea.com",
                "description": "Martinrea International Inc. is a diversified global automotive supplier that provides lightweight castings, aluminum blocks, structural components, and fluid management systems.",
                "industry": "Automotive Parts",
                "relevant_info": "Martinrea is a good fit due to its diverse operations and likely need for digital transformation across multiple sites."
            }
        },
        {
            "name": "Peter Cirulis",
            "title": "CFO",
            "email": "",
            "phone": "",
            "linkedin": "",
            "relevant_info": "As CFO, Peter Cirulis is responsible for financial strategies and would be interested in the financial optimization aspects of StreamERP.",
            "relevance_score": 93,
            "approach_reccomendation": "Emphasize how StreamERP can improve financial management and support growth initiatives.",
            "notes": "Peter Cirulis's recent appointment as CFO indicates his critical role in financial decision-making.",
            "source_urls": [
                "https://www.martinrea.com/press-release/peter-cirulis-appointed-chief-financial-officer-of-martinrea-international-inc/",
                "https://www.globaldata.com/company-profile/martinrea-international-inc/executives/"
            ],
            "company_info": {
                "name": "Martinrea International Inc.",
                "website": "https://www.martinrea.com",
                "description": "Martinrea International Inc. is a diversified global automotive supplier that provides lightweight castings, aluminum blocks, structural components, and fluid management systems.",
                "industry": "Automotive Parts",
                "relevant_info": "Martinrea is a good fit due to its diverse operations and likely need for digital transformation across multiple sites."
            }
        },
        {
            "name": "Skotti Fietsam",
            "title": "Senior Vice President, Supply Chain and CIO",
            "email": "s***@accuridecorp.com",
            "phone": "(812) ***-****",
            "linkedin": "",
            "relevant_info": "Skotti Fietsam handles supply chain and IT responsibilities, making them a relevant contact for StreamERP.",
            "relevance_score": 92,
            "approach_reccomendation": "Reach out to Skotti Fietsam by highlighting how StreamERP can improve supply chain efficiency and IT integration.",
            "notes": "Skotti's role involves both supply chain and IT, making them a key decision maker for ERP solutions.",
            "source_urls": [
                "https://www.accuridecorp.com/about-accuride/leadership"
            ],
            "company_info": {
                "name": "Accuride Corporation",
                "website": "https://www.accuridewheels.com",
                "description": "Accuride Corporation is a leading supplier of wheel end solutions to the global commercial vehicle industry.",
                "industry": "Automotive Parts",
                "relevant_info": "Accuride operates multiple production sites and is likely undergoing digital transformation in its operations."
            }
        },
        {
            "name": "Geoff Bruce",
            "title": "President of Accuride Wheels",
            "email": "g******@accuridecorp.com",
            "phone": "815288....",
            "linkedin": "",
            "relevant_info": "Geoff Bruce, as President of Accuride Wheels, could be interested in operational improvements offered by StreamERP.",
            "relevance_score": 94,
            "approach_reccomendation": "Emphasize how StreamERP can enhance operational efficiency and customer delivery in the wheel manufacturing sector.",
            "notes": "Geoff Bruce's role focuses on wheel operations, making him a potential decision maker for operational improvements.",
            "source_urls": [
                "https://thebrakereport.com/kent-jones-named-accuride-ceo/"
            ],
            "company_info": {
                "name": "Accuride Corporation",
                "website": "https://www.accuridewheels.com",
                "description": "Accuride Corporation is a leading supplier of wheel end solutions to the global commercial vehicle industry.",
                "industry": "Automotive Parts",
                "relevant_info": "Accuride operates multiple production sites and is likely undergoing digital transformation in its operations."
            }
        },
        {
            "name": "Kent Jones",
            "title": "Chief Executive Officer",
            "email": "",
            "phone": "",
            "linkedin": "",
            "relevant_info": "Kent Jones, as CEO, oversees strategic growth and innovation, which could include adopting StreamERP for operational enhancements.",
            "relevance_score": 95,
            "approach_reccomendation": "Approach Kent Jones by highlighting the strategic benefits of StreamERP in driving growth and innovation.",
            "notes": "Kent Jones's role as CEO makes him a key decision maker for strategic initiatives like adopting new ERP solutions.",
            "source_urls": [
                "https://www.accuridecorp.com/accuride-names-kent-jones-as-chief-executive-officer"
            ],
            "company_info": {
                "name": "Accuride Corporation",
                "website": "https://www.accuridewheels.com",
                "description": "Accuride Corporation is a leading supplier of wheel end solutions to the global commercial vehicle industry.",
                "industry": "Automotive Parts",
                "relevant_info": "Accuride operates multiple production sites and is likely undergoing digital transformation in its operations."
            }
        },
        {
            "name": "Jim Jarrell",
            "title": "CEO and President",
            "email": "jim.jarrell@linamar.com",
            "phone": "519-836-****",
            "linkedin": "",
            "relevant_info": "Jim Jarrell serves as the CEO and President of Linamar Corporation, responsible for overall strategic direction. His role involves overseeing major operations and strategic decisions which align with the need for ERP solutions.",
            "relevance_score": 87,
            "approach_reccomendation": "Approach Jim Jarrell by highlighting strategic partnerships or innovative solutions that align with Linamar's global expansion and operational goals.",
            "notes": "The phone number is partial and sourced from various directories. The LinkedIn profile was not found due to privacy settings or lack of public information.",
            "source_urls": [
                "https://www.linamar.com/team/jim-jarrell/",
                "https://contactout.com/Jim-Jarrell-85575078",
                "https://www.zoominfo.com/p/Jim-Jarrell/40390109"
            ],
            "company_info": {
                "name": "Linamar Corporation",
                "website": "https://www.linamar.com",
                "description": "Linamar Corporation is a diversified global manufacturing company of highly engineered products across its Powertrain and Driveline, Industrial, and Skyjack segments.",
                "industry": "Automotive Parts and Manufacturing",
                "relevant_info": "Linamar operates multiple production sites and is likely undergoing digital transformation in its operations."
            }
        },
        {
            "name": "Dale Schneider",
            "title": "Chief Financial Officer",
            "email": "d***@linamar.com",
            "phone": "(519) ***-****",
            "linkedin": "",
            "relevant_info": "Dale Schneider is the CFO of Linamar Corporation, playing a crucial role in financial planning and investment decisions. His focus on financial management aligns with the cost optimization features of StreamERP.",
            "relevance_score": 88,
            "approach_reccomendation": "I would approach Dale Schneider by emphasizing how StreamERP can help streamline financial operations and improve cost management across Linamar's operations.",
            "notes": "The phone number and email are partially masked for privacy.",
            "source_urls": [
                "https://www.linamar.com/report/linamar-corporation-announces-the-appointment-of-dale-schneider-as-chief-financial-officer/",
                "https://www.zoominfo.com/p/Dale-Schneider/1717114986"
            ],
            "company_info": {
                "name": "Linamar Corporation",
                "website": "https://www.linamar.com",
                "description": "Linamar Corporation is a diversified global manufacturing company of highly engineered products across its Powertrain and Driveline, Industrial, and Skyjack segments.",
                "industry": "Automotive Parts and Manufacturing",
                "relevant_info": "Linamar operates multiple production sites and is likely undergoing digital transformation in its operations."
            }
        },
        {
            "name": "Chris Merchant",
            "title": "Global Vice President Of Finance & Information Technology",
            "email": "",
            "phone": "519-836-XXXX",
            "linkedin": "",
            "relevant_info": "Chris Merchant has been with Linamar Corporation since 1999 and has served as Global Vice President of Finance & Information Technology.",
            "relevance_score": 82,
            "approach_reccomendation": "Contact through corporate channels or phone number provided. Consider reaching out via Linamar's corporate contact form referencing his title for appropriate routing.",
            "notes": "Email addresses were not publicly provided in full; phone number partially obtained but not complete.",
            "source_urls": [
                "https://rocketreach.co/chris-merchant-email_25232531",
                "https://theorg.com/org/linamar-corp/org-chart/chris-merchant",
                "https://www.cpaontario.ca/protecting-the-public/directories/member/merchant-1l5c2b"
            ],
            "company_info": {
                "name": "Linamar Corporation",
                "website": "https://www.linamar.com",
                "description": "Linamar Corporation is a diversified global manufacturing company of highly engineered products across its Powertrain and Driveline, Industrial, and Skyjack segments.",
                "industry": "Automotive Parts and Manufacturing",
                "relevant_info": "Linamar operates multiple production sites and is likely undergoing digital transformation in its operations."
            }
        },
        {
            "name": "Roxanne Rose",
            "title": "Vice President, Global Human Resources",
            "email": "Roxanne.Rose@linamar.com",
            "phone": "519-836-7550",
            "linkedin": "",
            "relevant_info": "Roxanne Rose is a seasoned professional with extensive experience in Human Resources. She is currently serving as the Vice President, Global Human Resources at Linamar Corporation.",
            "relevance_score": 90,
            "approach_reccomendation": "I would approach Roxanne Rose by highlighting any expertise or solutions relevant to her role in Human Resources, such as innovative HR technologies or strategies for organizational development.",
            "notes": "The phone number and email might be used for general inquiries or accessibility feedback rather than direct personal contact.",
            "source_urls": [
                "https://www.linamar.com/team/roxanne-rose/",
                "https://rocketreach.co/roxanne-rose-email_7886431",
                "https://www.linamar.com/wp-content/uploads/2024/01/Updated-Linamar-Feedback-Form.pdf"
            ],
            "company_info": {
                "name": "Linamar Corporation",
                "website": "https://www.linamar.com",
                "description": "Linamar Corporation is a diversified global manufacturing company of highly engineered products across its Powertrain and Driveline, Industrial, and Skyjack segments.",
                "industry": "Automotive Parts and Manufacturing",
                "relevant_info": "Linamar operates multiple production sites and is likely undergoing digital transformation in its operations."
            }
        },
        {
            "name": "Mark Stoddart",
            "title": "Chief Technology Officer & Executive Vice President of Sales and Marketing",
            "email": "m***@linamar.com",
            "phone": "",
            "linkedin": "",
            "relevant_info": "Mark Stoddart is a seasoned executive with extensive experience in the automotive sector, joining Linamar in 1985.",
            "relevance_score": 84,
            "approach_reccomendation": "I would approach Mark Stoddart by highlighting expertise in automotive technology and marketing strategies, emphasizing how your solutions align with Linamar's focus on innovative manufacturing solutions.",
            "notes": "I couldn't find a complete, verified email address or a LinkedIn profile.",
            "source_urls": [
                "https://www.linamar.com/team/mark-stoddart/",
                "https://www.enertechcapital.com/post/enertech-capital-adds-linamar-executive-mark-stoddart-to-mobility-advisory-board",
                "https://www.zoominfo.com/p/Mark-Stoddart/265096096"
            ],
            "company_info": {
                "name": "Linamar Corporation",
                "website": "https://www.linamar.com",
                "description": "Linamar Corporation is a diversified global manufacturing company of highly engineered products across its Powertrain and Driveline, Industrial, and Skyjack segments.",
                "industry": "Automotive Parts and Manufacturing",
                "relevant_info": "Linamar operates multiple production sites and is likely undergoing digital transformation in its operations."
            }
        }
    ]
}
""".strip()

# Load config once at startup
config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

# dictionary to store the final results, key is userId, value is the leads list
final_results = {}

# Initialize agent once and store as global
intakeAgent = IntakeAgent()
companyResearchAgent = CompanyResearchAgent()
peopleFinderAgent = PeopleFinderAgent()
contactEnrichmentAgent = ContactEnrichmentAgent()
leadScoringAgent = LeadScoringAgent()

@app.post("/chat")
async def chat(request: Request):
    """API Endpoint that handles intake data and responds to user queries"""
    data = await request.json()
    user_query = data.get("message", "")
    user_agent = request.headers.get("user-agent")

    # Process the message and get response
    results = await intakeAgent.process_message(user_query, user_agent)
    print("-------------results-------------------")
    print(results)

    if results["complete"]:
        asyncio.create_task(processIntakeData(user_agent))
    
    return results

@app.post("/new_session")
async def newSession(request: Request):
    """API Endpoint that clears the conversation history and starts a new session"""
    data = await request.json()
    user_agent = request.headers.get("user-agent")

    should_start_new_session = data.get("new", "")

    results = { "response": "Error" }

    if (should_start_new_session == "true"):
        intakeAgent.message_history[user_agent] = []
        if user_agent in final_results:
            del final_results[user_agent]
        results = { "response": "session restarted" }
    else:
        results = { "response": "session not restarted" }

    print("-------------results-------------------")
    print(results)

    return results

async def processIntakeData(userId: str):
    return
    print("-------------started lead generation-------------------")
    intakeInfoString = intakeAgent.intake_data
    # get company list
    # companyListString = await companyResearchAgent.process_message(intakeAgent, intakeInfoString)
    companyListString = companyTestData

    print("-------------Company List results-------------------")
    print(companyListString)

    # # get people list
    # companyListAndPeopleString = await peopleFinderAgent.process_message(companyResearchAgent, intakeInfoString, companyListString)
    # print("-------------Company List and people results-------------------")
    # print(companyListAndPeopleString)

    # enrich people list
    # companyListAndPeopleStringEnriched = await contactEnrichmentAgent.process_message(peopleFinderAgent, companyListAndPeopleString)
    companyListAndPeopleStringEnriched = companyListWithPeopleTestData

    # score leads
    leadsListString = await leadScoringAgent.process_message(contactEnrichmentAgent, intakeInfoString, companyListAndPeopleStringEnriched)

    print("-------------Leads List results-------------------")
    print(leadsListString)
    final_results[userId] = leadsListString
    return




@app.get("/results")
async def getResults(request: Request):
    """API Endpoint that returns the leads list for the user"""

    # user_agent = request.headers.get("user-agent")

    # if user_agent in final_results:
    #     return final_results[user_agent]

    return leadsTestData
    # return "Leads haven't been generated yet"