// Auxiliary driver for the Pack AA kinematic closure study.
//
// This is a NEW, standalone tool that lives entirely under
// studies/pack_aa_kinematic_validation/. It does not modify, replace, or
// share a binary with the canonical pack_aa/bin/.pack_aa_driver or
// pack_aa/src/pack_aa_driver.cc. It reproduces the same physics
// configuration approach (LHE input, h2 lifetime/decay setup via
// Pythia8's particle-data API) so that its "D1" mode is physically
// equivalent to canonical Pack AA, while additionally dumping the full
// final-state particle listing needed for recoil (8.4) and extra-photon
// (8.5) accounting, which the canonical truth_jsonl schema does not carry.
#include "Pythia8/Pythia.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace Pythia8;

struct Channel {
  double br;
  std::vector<int> daughters;
};

static std::string usage() {
  return "usage: kinematic_validation_driver --lhe FILE --out JSONL --events N --seed N "
         "--mass GEV --ctau MM --is-resonance 0|1 --production-events N "
         "--channels BR:PDG,PDG[;...] [--cmnd FILE]";
}

static std::string value(int argc, char** argv, const std::string& key) {
  for (int i = 1; i + 1 < argc; ++i)
    if (argv[i] == key) return argv[i + 1];
  throw std::runtime_error("missing " + key + "\n" + usage());
}

static bool hasArg(int argc, char** argv, const std::string& key) {
  for (int i = 1; i < argc; ++i) if (argv[i] == key) return true;
  return false;
}

static std::vector<Channel> parseChannels(const std::string& text) {
  std::vector<Channel> channels;
  std::stringstream all(text);
  std::string item;
  while (std::getline(all, item, ';')) {
    std::stringstream fields(item);
    std::string brText, pdgText;
    if (!std::getline(fields, brText, ':') || !std::getline(fields, pdgText))
      throw std::runtime_error("bad channel: " + item);
    Channel channel{std::stod(brText), {}};
    std::stringstream pdgs(pdgText);
    std::string pdg;
    while (std::getline(pdgs, pdg, ',')) channel.daughters.push_back(std::stoi(pdg));
    if (channel.daughters.empty()) throw std::runtime_error("empty channel: " + item);
    channels.push_back(channel);
  }
  if (channels.empty()) throw std::runtime_error("no decay channels");
  return channels;
}

static int configuredChannel(const std::vector<int>& daughters,
                             const std::vector<Channel>& channels) {
  for (std::size_t i = 0; i < channels.size(); ++i) {
    std::vector<int> left = daughters, right = channels[i].daughters;
    std::sort(left.begin(), left.end());
    std::sort(right.begin(), right.end());
    if (left == right) return static_cast<int>(i);
  }
  return -1;
}

// Walk the mother chain of a final-state particle back to the beam. Returns
// the index (0 or 1, ordinal position among the two physical h2 for this
// event) of the h2 ancestor if found, else -1. Loop-protected with a visited
// set since Pythia8 histories can revisit indices through mother2 branches.
static int h2Ancestor(const Event& event, int index, const std::vector<int>& physicalH2) {
  std::set<int> visited;
  std::vector<int> stack{index};
  while (!stack.empty()) {
    int i = stack.back();
    stack.pop_back();
    if (i <= 0 || visited.count(i)) continue;
    visited.insert(i);
    for (std::size_t h = 0; h < physicalH2.size(); ++h)
      if (physicalH2[h] == i) return static_cast<int>(h);
    const Particle& p = event[i];
    if (p.mother1() > 0) stack.push_back(p.mother1());
    if (p.mother2() > 0 && p.mother2() != p.mother1()) stack.push_back(p.mother2());
  }
  return -1;
}

static void writeParticle(std::ostream& out, const Particle& p, int h2Anc) {
  out << "{\"index\":" << p.index() << ",\"id\":" << p.id() << ",\"status\":" << p.status()
      << ",\"mother1\":" << p.mother1() << ",\"mother2\":" << p.mother2()
      << ",\"px\":" << p.px() << ",\"py\":" << p.py() << ",\"pz\":" << p.pz()
      << ",\"e\":" << p.e() << ",\"m\":" << p.m() << ",\"h2Ancestor\":" << h2Anc << "}";
}

int main(int argc, char** argv) {
  try {
    const std::string lhe = value(argc, argv, "--lhe");
    const std::string output = value(argc, argv, "--out");
    const int events = std::stoi(value(argc, argv, "--events"));
    const int seed = std::stoi(value(argc, argv, "--seed"));
    const double mass = std::stod(value(argc, argv, "--mass"));
    const double ctau = std::stod(value(argc, argv, "--ctau"));
    const int productionEvents = std::stoi(value(argc, argv, "--production-events"));
    const std::string adapter = hasArg(argc, argv, "--cmnd") ? value(argc, argv, "--cmnd") : "";
    const bool isResonance = std::stoi(value(argc, argv, "--is-resonance")) != 0;
    const std::vector<Channel> channels = parseChannels(value(argc, argv, "--channels"));
    if (events <= 0 || productionEvents <= 0 || mass <= 0.0 || ctau <= 0.0)
      throw std::runtime_error("invalid numeric input");

    Pythia pythia;
    pythia.readString("Beams:frameType = 4");
    pythia.readString("Beams:LHEF = " + lhe);
    pythia.readString("SLHA:readFrom = 0");
    pythia.readString("LesHouches:setLifetime = 2");
    pythia.readString("Random:setSeed = on");
    pythia.readString("Random:seed = " + std::to_string(seed));
    pythia.readString("Next:numberShowEvent = 0");
    pythia.readString("Next:numberShowInfo = 0");
    pythia.readString("Next:numberShowProcess = 0");
    const double physicalWidth = 1.973269804e-13 / ctau;
    const double width = isResonance ? std::max(physicalWidth, 1e-9) : physicalWidth;
    pythia.readString("9000006:all = h2 h2 1 0 0 " + std::to_string(mass) + " " + std::to_string(width) + " 0 0 " + std::to_string(ctau));
    pythia.readString("9000006:isResonance = " + std::string(isResonance ? "true" : "false"));
    pythia.readString("9000006:mayDecay = true");
    pythia.readString("9000006:tau0 = " + std::to_string(ctau));
    pythia.readString("ParticleDecays:limitTau0 = off");
    for (const Channel& channel : channels) {
      std::ostringstream setting;
      setting << "9000006:addChannel = 1 " << std::setprecision(17) << channel.br
              << ' ' << (isResonance ? 101 : 0);
      for (int daughter : channel.daughters) setting << ' ' << daughter;
      pythia.readString(setting.str());
    }
    if (!adapter.empty() && !pythia.readFile(adapter)) throw std::runtime_error("adapter .cmnd read failed");
    if (!pythia.init()) throw std::runtime_error("Pythia init failed");
    ParticleDataEntryPtr h2Data = pythia.particleData.particleDataEntryPtr(9000006);
    h2Data->clearChannels();
    for (const Channel& channel : channels) {
      h2Data->addChannel(1, channel.br, isResonance ? 101 : 0,
                         channel.daughters.size() > 0 ? channel.daughters[0] : 0,
                         channel.daughters.size() > 1 ? channel.daughters[1] : 0,
                         channel.daughters.size() > 2 ? channel.daughters[2] : 0,
                         channel.daughters.size() > 3 ? channel.daughters[3] : 0);
    }
    h2Data->rescaleBR();
    h2Data->setMayDecay(true);
    h2Data->setTau0(ctau);
    h2Data->setMWidth(width);
    h2Data->setTauCalc(!isResonance);
    pythia.particleData.resInit(9000006);
    h2Data->setTau0(ctau);

    std::ofstream out(output);
    if (!out) throw std::runtime_error("cannot open output " + output);
    out << std::setprecision(17);
    int processed = 0;
    int failed = 0;
    while (processed < events) {
      if (!pythia.next()) {
        ++failed;
        break;
      }
      ++processed;
      const int productionEventId = (processed - 1) % productionEvents + 1;
      const int replicaId = (processed - 1) / productionEvents;

      // Physical h2's: those whose direct daughters match a configured
      // channel. Kept in ascending event-index order, which is the same
      // ordinal convention as the canonical pack_aa_driver and matches LHE
      // particle-line order (validated empirically against the LHE record).
      std::vector<int> h2Indices;
      for (int i = 0; i < pythia.event.size(); ++i)
        if (pythia.event[i].id() == 9000006) h2Indices.push_back(i);
      std::vector<int> physicalH2;
      for (int index : h2Indices) {
        std::vector<int> daughters;
        for (int daughter : pythia.event[index].daughterList()) daughters.push_back(pythia.event[daughter].id());
        if (configuredChannel(daughters, channels) >= 0) physicalH2.push_back(index);
      }

      out << "{\"schema\":\"kinematic_validation.truth.v1\",\"event\":" << processed
          << ",\"production_event_id\":" << productionEventId
          << ",\"replica_id\":" << replicaId
          << ",\"pythia_seed\":" << seed
          << ",\"weight\":" << pythia.info.weight()
          << ",\"h2\":[";
      for (std::size_t h = 0; h < physicalH2.size(); ++h) {
        const Particle& p = pythia.event[physicalH2[h]];
        if (h) out << ',';
        std::vector<int> daughterIdx = p.daughterList();
        out << "{\"ordinal\":" << h << ",\"index\":" << p.index()
            << ",\"px\":" << p.px() << ",\"py\":" << p.py() << ",\"pz\":" << p.pz()
            << ",\"e\":" << p.e() << ",\"m\":" << p.m()
            << ",\"xProd\":" << p.xProd() << ",\"yProd\":" << p.yProd()
            << ",\"zProd\":" << p.zProd() << ",\"tProd\":" << p.tProd()
            << ",\"xDec\":" << p.xDec() << ",\"yDec\":" << p.yDec()
            << ",\"zDec\":" << p.zDec() << ",\"tDec\":" << p.tDec()
            << ",\"properLength_mm\":" << p.tau()
            << ",\"directDaughterIndices\":[";
        for (std::size_t j = 0; j < daughterIdx.size(); ++j) { if (j) out << ','; out << daughterIdx[j]; }
        out << "],\"directDaughters\":[";
        for (std::size_t j = 0; j < daughterIdx.size(); ++j) {
          if (j) out << ',';
          writeParticle(out, pythia.event[daughterIdx[j]], static_cast<int>(h));
        }
        out << "]}";
      }
      out << "],\"final_state\":[";
      bool firstFinal = true;
      for (int i = 0; i < pythia.event.size(); ++i) {
        const Particle& p = pythia.event[i];
        if (!p.isFinal()) continue;
        const int anc = h2Ancestor(pythia.event, i, physicalH2);
        if (!firstFinal) out << ',';
        firstFinal = false;
        writeParticle(out, p, anc);
      }
      out << "]}\n";
    }
    out.close();
    return processed == events && failed == 0 ? 0 : 3;
  } catch (const std::exception& error) {
    std::cerr << "kinematic_validation_driver: " << error.what() << '\n';
    return 3;
  }
}
