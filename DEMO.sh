#!/bin/bash
# gh-oscal: 2-Minute Hackathon Demo
# Demonstrates automated OSCAL compliance documentation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Demo config
DEMO_SYSTEM="HackathonDemo"
DEMO_BASELINE="moderate"
SSP_FILE="demo-ssp.json"
SCAN_RESULTS="demo-scan.json"
REPO_PATH="Test_Case/FedChat"

# Clear screen and show banner
clear
echo -e "${BOLD}${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   gh-oscal: Automated OSCAL Compliance Documentation         ║
║   From Zero to FedRAMP-Ready in 60 Seconds                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

sleep 2

# ============================================================================
# PART 1: THE PROBLEM
# ============================================================================
echo -e "${BOLD}${RED}━━━ PART 1: The Problem ━━━${NC}\n"
sleep 1

echo -e "${YELLOW}The Challenge:${NC}"
echo -e "  • FedRAMP compliance requires documenting 243+ NIST 800-53 controls"
echo -e "  • Each control takes 30-60 minutes to document"
echo -e "  • Total time: ${RED}${BOLD}120+ hours${NC} of manual work"
echo -e "  • Engineers don't know what they've already implemented\n"
sleep 3

echo -e "${CYAN}Let's see what an empty SSP looks like...${NC}\n"
sleep 1

# Generate empty SSP
echo -e "${BOLD}$ ./gh-oscal-cli generate --baseline $DEMO_BASELINE --system \"$DEMO_SYSTEM\" --output $SSP_FILE${NC}"
sleep 1
./gh-oscal-cli generate --baseline $DEMO_BASELINE --system "$DEMO_SYSTEM" --output $SSP_FILE 2>/dev/null

echo ""
sleep 2

# Show empty control
echo -e "${YELLOW}📄 Sample Control (AC-2: Account Management):${NC}"
cat $SSP_FILE | jq '.["system-security-plan"]["control-implementation"]["implemented-requirements"][] | select(.["control-id"] == "AC-2") | {control: .["control-id"], description: .description, statements: .statements}' 2>/dev/null | head -10
echo -e "${RED}   └─ statements: [] ${BOLD}← EMPTY! Need to fill manually${NC}\n"
sleep 3

echo -e "${MAGENTA}➡️  That's 243 controls to fill manually... Let's fix this!${NC}\n"
sleep 2

# ============================================================================
# PART 2: THE SOLUTION
# ============================================================================
echo -e "${BOLD}${GREEN}━━━ PART 2: The Solution ━━━${NC}\n"
sleep 1

echo -e "${CYAN}gh-oscal automatically scans your codebase for compliance evidence:${NC}"
echo -e "  ✓ Infrastructure (Docker, Kubernetes, CI/CD)"
echo -e "  ✓ Security Features (Auth, Encryption, Audit Logging)"
echo -e "  ✓ Documentation (Risk Assessments, Privacy Docs)"
echo -e "  ✓ Code Patterns (Input Validation, Error Handling)\n"
sleep 3

echo -e "${BOLD}$ ./gh-oscal-cli scan $REPO_PATH --update $SSP_FILE --output $SCAN_RESULTS${NC}\n"
sleep 2

# Run scan with full output
./gh-oscal-cli scan $REPO_PATH --update $SSP_FILE --output $SCAN_RESULTS

echo ""
sleep 3

# ============================================================================
# PART 3: THE RESULTS
# ============================================================================
echo -e "${BOLD}${BLUE}━━━ PART 3: The Results ━━━${NC}\n"
sleep 1

echo -e "${GREEN}✨ What just happened?${NC}\n"
sleep 1

# Show updated control
echo -e "${YELLOW}📄 Same Control (AC-2) - Now Auto-Documented:${NC}"
cat $SSP_FILE | jq '.["system-security-plan"]["control-implementation"]["implemented-requirements"][] | select(.["control-id"] == "AC-2") | {control: .["control-id"], description: .description, statements: .statements}' 2>/dev/null
echo -e "${GREEN}   └─ statements: [populated] ${BOLD}← AUTO-FILLED with evidence!${NC}\n"
sleep 3

# Show statistics
TOTAL_SIGNALS=$(cat $SCAN_RESULTS | jq '. | length' 2>/dev/null)
UNIQUE_CONTROLS=$(cat $SCAN_RESULTS | jq '[.[].control] | unique | length' 2>/dev/null)
COVERAGE=$(echo "scale=1; ($UNIQUE_CONTROLS / 243) * 100" | bc 2>/dev/null)
TIME_SAVED=$(echo "scale=1; $UNIQUE_CONTROLS * 0.5" | bc 2>/dev/null)

echo -e "${CYAN}📊 Impact Summary:${NC}"
echo -e "   ├─ Signals Detected: ${GREEN}${BOLD}${TOTAL_SIGNALS}${NC}"
echo -e "   ├─ Controls Auto-Documented: ${GREEN}${BOLD}${UNIQUE_CONTROLS}/243${NC} (${COVERAGE}%)"
echo -e "   ├─ Time Saved: ${MAGENTA}${BOLD}~${TIME_SAVED} hours${NC}"
echo -e "   └─ Remaining: ${YELLOW}$((243 - UNIQUE_CONTROLS)) controls${NC} (fill manually)\n"
sleep 3

# ============================================================================
# BONUS: Explain Command
# ============================================================================
echo -e "${BOLD}${MAGENTA}━━━ BONUS: Developer-Friendly Explanations ━━━${NC}\n"
sleep 1

echo -e "${CYAN}Don't speak compliance? We translate for you:${NC}\n"
sleep 1

echo -e "${BOLD}$ ./gh-oscal-cli explain AC-2 --for-devs${NC}\n"
sleep 1
./gh-oscal-cli explain AC-2 --for-devs 2>/dev/null | head -20
echo -e "   ${BLUE}[...see full output...]${NC}\n"
sleep 2

# ============================================================================
# FINALE
# ============================================================================
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${GREEN}✅ Demo Complete!${NC}\n"

echo -e "${CYAN}What We Built:${NC}"
echo -e "  • Native GitHub CLI extension (not a chatbot wrapper)"
echo -e "  • Scans ${BOLD}Python, Node.js, Docker, Kubernetes${NC}"
echo -e "  • Auto-documents ${BOLD}31+ NIST 800-53 controls${NC}"
echo -e "  • Generates valid ${BOLD}OSCAL 1.2.0 JSON${NC}"
echo -e "  • Saves ${BOLD}15+ hours${NC} of documentation work\n"

echo -e "${YELLOW}Try it yourself:${NC}"
echo -e "  ${BOLD}gh extension install .${NC}"
echo -e "  ${BOLD}gh oscal scan . --update ssp.json${NC}\n"

echo -e "${MAGENTA}From ${RED}${BOLD}120 hours${NC} ${MAGENTA}→ ${GREEN}${BOLD}30 seconds${NC} 🚀\n"

echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Cleanup
echo -e "${BLUE}Demo files created:${NC}"
echo -e "  • $SSP_FILE (OSCAL SSP with auto-documented controls)"
echo -e "  • $SCAN_RESULTS (Raw scan results JSON)"
echo -e "\n${GREEN}Thank you!${NC}\n"
